#!/usr/bin/env bash
# Único caminho de commit (AGENTS §5; ARQUITETURA §2.1; brief 001).
# Uso: scripts/entregar.sh <NNN>
# Lê o manifesto do relatório docs/docs/doc_<NNN>_*.md, roda o gate,
# confere que não há arquivo fora do manifesto, adiciona arquivo por arquivo,
# commita com o texto do manifesto e envia o ramo atual, se houver remoto.
set -euo pipefail

falhar() {
    echo "entregar.sh: $*" >&2
    exit 1
}

numero="${1:-}"
[[ "$numero" =~ ^[0-9]{3}$ ]] || falhar "uso: scripts/entregar.sh <NNN> (número do brief com três dígitos)"

raiz="$(git rev-parse --show-toplevel)" || falhar "não estou dentro de um repositório git"
cd "$raiz"

shopt -s nullglob
relatorios=(docs/docs/doc_"${numero}"_*.md)
shopt -u nullglob
[[ ${#relatorios[@]} -eq 1 ]] ||
    falhar "é preciso exatamente um relatório docs/docs/doc_${numero}_*.md (achei ${#relatorios[@]})"
relatorio="${relatorios[0]}"

# Manifesto: o primeiro bloco cercado por três crases depois da linha
# "- Lista de arquivos para `git add` e texto do commit:".
manifesto="$(awk '
    index($0, "- Lista de arquivos para `git add` e texto do commit:") == 1 { achou = 1; next }
    achou && !dentro && /^[[:space:]]*```/ { dentro = 1; next }
    dentro && /^[[:space:]]*```/ { exit }
    dentro { print }
' "$relatorio")"

arquivos=()
remover=()
texto_commit=""
na_lista=1
while IFS= read -r linha || [[ -n "$linha" ]]; do
    if [[ $na_lista -eq 1 ]]; then
        if [[ -z "${linha//[[:space:]]/}" ]]; then
            na_lista=0
            continue
        fi
        if [[ "$linha" == remover:* ]]; then
            caminho="${linha#remover:}"
            caminho="${caminho#"${caminho%%[![:space:]]*}"}"
            remover+=("$caminho")
        else
            arquivos+=("$linha")
        fi
    else
        texto_commit+="$linha"$'\n'
    fi
done <<<"$manifesto"

# Tira linhas em branco do começo e do fim do texto do commit.
texto_commit="$(printf '%s' "$texto_commit" | sed -e '/./,$!d')"
[[ ${#arquivos[@]} -gt 0 || ${#remover[@]} -gt 0 ]] || falhar "manifesto sem arquivos em $relatorio"
[[ -n "${texto_commit//[[:space:]]/}" ]] || falhar "manifesto sem texto de commit em $relatorio"

# Mudanças pendentes no repositório (alteradas, novas, removidas).
declare -A mudados=()
while IFS= read -r -d '' entrada; do
    estado="${entrada:0:2}"
    caminho="${entrada:3}"
    mudados["$caminho"]=1
    if [[ "$estado" == R* || "$estado" == C* ]]; then
        IFS= read -r -d '' origem || true
        mudados["$origem"]=1
    fi
done < <(git status --porcelain=v1 -z --untracked-files=all)

declare -A no_manifesto=()
for caminho in "${arquivos[@]}"; do
    [[ -n "${mudados[$caminho]:-}" ]] || falhar "caminho do manifesto sem mudança: $caminho"
    no_manifesto["$caminho"]=1
done
for caminho in "${remover[@]}"; do
    git ls-files --error-unmatch -- "$caminho" >/dev/null 2>&1 ||
        falhar "remover: $caminho não é arquivo rastreado"
    no_manifesto["$caminho"]=1
done

# O gate precisa estar verde antes de qualquer add.
if ! "$raiz/scripts/verificar.sh"; then
    falhar "gate vermelho (scripts/verificar.sh falhou); nada foi commitado"
fi

# Depois do gate, nenhum arquivo alterado ou novo fora do manifesto.
fora=()
while IFS= read -r -d '' entrada; do
    estado="${entrada:0:2}"
    caminho="${entrada:3}"
    [[ -n "${no_manifesto[$caminho]:-}" ]] || fora+=("$caminho")
    if [[ "$estado" == R* || "$estado" == C* ]]; then
        IFS= read -r -d '' origem || true
        [[ -n "${no_manifesto[$origem]:-}" ]] || fora+=("$origem")
    fi
done < <(git status --porcelain=v1 -z --untracked-files=all)
if [[ ${#fora[@]} -gt 0 ]]; then
    printf 'entregar.sh: arquivo alterado ou novo fora do manifesto: %s\n' "${fora[@]}" >&2
    exit 1
fi

for caminho in "${arquivos[@]}"; do
    git add -- "$caminho"
done
for caminho in "${remover[@]}"; do
    git rm -q -- "$caminho"
done

arquivo_texto="$(mktemp)"
trap 'rm -f "$arquivo_texto"' EXIT
printf '%s\n' "$texto_commit" >"$arquivo_texto"
git commit -q -F "$arquivo_texto"
echo "entregar.sh: commit $(git rev-parse --short HEAD) feito com ${#arquivos[@]} arquivo(s) e ${#remover[@]} remoção(ões)."

if [[ -n "$(git remote)" ]]; then
    espera=2
    for tentativa in 1 2 3 4; do
        if git push -u origin HEAD; then
            echo "entregar.sh: ramo enviado."
            exit 0
        fi
        if [[ $tentativa -lt 4 ]]; then
            echo "entregar.sh: envio falhou (tentativa $tentativa de 4); nova tentativa em ${espera}s." >&2
            sleep "$espera"
            espera=$((espera * 2))
        fi
    done
    falhar "o commit foi feito, mas o envio falhou depois de 4 tentativas"
fi
echo "entregar.sh: repositório sem remoto; nada enviado."
