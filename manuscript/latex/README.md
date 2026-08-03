# LaTeX source — IEEE Journal of Photovoltaics submission

## Build

```bash
./build.sh          # both documents
./build.sh main     # manuscript only
./build.sh supp     # supplementary only
./build.sh clean    # remove .aux/.bbl/.log artefacts
```

Each run does `pdflatex → bibtex → pdflatex → pdflatex`, so citations and
cross-references resolve. Output: `main.pdf`, `supplementary.pdf`.

## Files

| file | purpose |
|---|---|
| `main.tex` | manuscript, two-column IEEEtran |
| `supplementary.tex` | supplement, single-column, S-numbered floats |
| `references.bib` | BibTeX database, 46 entries |
| `IEEEtran.cls` | official IEEE class (from the IEEE template pack) |
| `figures/` | main-text figures, vector PDF |
| `figures_si/` | supplementary figures, vector PDF |
| `build.sh` | build driver |

## Editorial flags

Both documents define `\edit{...}`, which typesets in **red**. These mark
items needing manual attention (missing dates, author photographs, unverified
citations). To hide them all at once, change one line near the top of each
file:

```latex
\editstrue    →    \editsfalse
```

Do not submit with `\editstrue`.

## Bibliography style

The documents prefer `IEEEtran.bst` and fall back to `ieeetr.bst`
automatically:

```latex
\IfFileExists{IEEEtran.bst}{\bibliographystyle{IEEEtran}}{\bibliographystyle{ieeetr}}
```

`IEEEtran.bst` is the correct IEEE style and gives proper reference
formatting. It ships in `texlive-publishers` — see below. Until it is
installed the build uses `ieeetr.bst`, which is close but not identical.

## Incomplete references

`references.bib` entries whose data could not be verified carry a
`note = {INCOMPLETE: ...}` field saying exactly what is missing. **Those notes
print in the reference list on purpose**, so an incomplete entry cannot reach a
referee unnoticed. Delete the note once the field is supplied. The full audit
is in `../../audit/CITATION_VERIFICATION.md`.

## Author photographs

Biographies currently use `IEEEbiographynophoto`. To add photographs, place
`mohiuddin.jpg` and `kabir.jpg` beside `main.tex` and swap in the commented
`\begin{IEEEbiography}[...]` lines directly above each entry. IEEE
specification: 1 in × 1.25 in, 300 dpi minimum, TIFF or high-quality JPEG,
head-and-shoulders.

## Installing the full TeX Live

The build works with the packages already present. For the complete set —
including `IEEEtran.bst`, `siunitx`, `latexmk` and `biber` — run:

```bash
sudo apt update
sudo apt install texlive-full latexmk biber
```

That is roughly 5–6 GB. A smaller sufficient subset:

```bash
sudo apt install texlive-latex-extra texlive-publishers texlive-science latexmk
```

`texlive-publishers` is the one that provides `IEEEtran.bst`.

On Windows, install MiKTeX (<https://miktex.org>) instead; it fetches missing
packages on demand, so no explicit package selection is needed.

## Editors

Any LaTeX editor works. TeXstudio is a good local choice
(`sudo apt install texstudio`); it picks up `build.sh` output automatically and
has a built-in PDF viewer with forward/inverse search.
