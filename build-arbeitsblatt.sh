#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

for command in pandoc xelatex; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Fehlt: $command. Installiere auf Ubuntu: sudo apt install pandoc texlive-xetex texlive-latex-extra fonts-dejavu" >&2
    exit 1
  fi
done

build_pdf() {
  local input_file="$1"
  local output_file="$2"

  pandoc \
    --from=markdown \
    --number-sections \
    --pdf-engine=xelatex \
    --resource-path=docs \
    --include-in-header=docs/arbeitsblatt-header.tex \
    -V documentclass=article \
    -V fontsize=11pt \
    -V papersize=a4 \
    -V geometry:margin=2.5cm \
    -V mainfont="DejaVu Serif" \
    -V monofont="DejaVu Sans Mono" \
    -V colorlinks=true \
    -V linkcolor=black \
    -V urlcolor=black \
    -o "$output_file" \
    "$input_file"

  echo "Erstellt: $output_file"
  pdfinfo "$output_file" | awk -F: '/^Pages:|^File size:/ {gsub(/^ +/, "", $2); print $1 ": " $2}'
}

build_pdf docs/arbeitsblatt-sus.md docs/arbeitsblatt-sus.pdf
build_pdf docs/arbeitsblatt-sus-loesungen.md docs/arbeitsblatt-sus-loesungen.pdf
