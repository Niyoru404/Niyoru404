#!/usr/bin/env bash
# Troca a imagem quadrada do cartão "Hii There!" e publica no perfil.
# Uso: ~/Niyoru404/trocar-imagem.sh ~/Downloads/minha-imagem.png
# Imagens que não são quadradas são cortadas no centro. GIF animado vira imagem parada.
set -euo pipefail

[ $# -eq 1 ] && [ -f "$1" ] || { echo "Uso: $0 caminho/da/imagem" >&2; exit 1; }
cd "$(dirname "$(readlink -f "$0")")"

tmp=$(mktemp --suffix=.png)
trap 'rm -f "$tmp"' EXIT
ffmpeg -y -v error -i "$1" -vf "crop='min(iw,ih)':'min(iw,ih)',scale=320:320" -frames:v 1 -update 1 "$tmp"

python3 - "$tmp" <<'PY'
import base64, re, sys
data = base64.b64encode(open(sys.argv[1], "rb").read()).decode()
svg = open("assets/hello.svg", encoding="utf-8").read()
svg, n = re.subn(r'(<image id="avatar"[^>]*href=")[^"]*', rf"\g<1>data:image/png;base64,{data}", svg)
if n != 1:
    sys.exit("Imagem do cartão não encontrada em assets/hello.svg")
open("assets/hello.svg", "w", encoding="utf-8").write(svg)
PY

[ -z "${SEM_ENVIAR:-}" ] || exit 0
git add assets/hello.svg
git commit -qm "Troca a imagem do perfil"
git pull -q --rebase
git push -q
echo "Pronto! Pode levar alguns minutos para aparecer no perfil."
