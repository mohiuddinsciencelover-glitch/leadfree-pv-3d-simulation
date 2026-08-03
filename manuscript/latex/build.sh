#!/usr/bin/env bash
# Build the IEEE JPV manuscript and supplement.
#   ./build.sh            build both
#   ./build.sh main       build only the manuscript
#   ./build.sh clean      remove build artefacts
set -u
cd "$(dirname "$0")"
clean() { rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot; }
one() {
  local j=$1
  echo "### $j"
  pdflatex -interaction=nonstopmode -halt-on-error "$j" >/dev/null 2>&1
  bibtex "$j" >/dev/null 2>&1
  pdflatex -interaction=nonstopmode -halt-on-error "$j" >/dev/null 2>&1
  pdflatex -interaction=nonstopmode "$j" > "$j.build.log" 2>&1
  if [ -f "$j.pdf" ]; then
    echo "    OK  -> $j.pdf  ($(pdfinfo "$j.pdf" 2>/dev/null | awk '/^Pages/{print $2}') pages)"
    grep -cE "^(LaTeX|Package) Warning: (Citation|Reference)" "$j.build.log" 2>/dev/null \
      | awk '{if($1>0) print "    "$1" undefined citation/reference warnings"}'
  else
    echo "    FAILED -- see $j.build.log"; grep -m5 -E "^! " "$j.build.log"
  fi
}
case "${1:-all}" in
  clean) clean; echo "cleaned";;
  main)  one main;;
  supp)  one supplementary;;
  *)     one main; [ -f supplementary.tex ] && one supplementary;;
esac
