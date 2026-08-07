# Reproducing this study

This document reproduces every number in *"Interface Band Offsets as the Common Limit Across Four Lead-Free
Perovskite Solar-Cell Absorbers: A Coupled Opto-Electrical COMSOL Study"* from the
archived inputs. It is written to be followed by someone who has COMSOL and has
never seen this project.

Read Section 6 (**Traps**) before running anything. Four of them silently
produce plausible but wrong answers, and each cost significant time here.

---

## 1. What is in this archive

```
data/
  optical_constants/       n,k for every material (lambda_um, n, k; % header)
  reference_spectra/       AM1.5G ASTM G173 global tilt
results/
  optical/                 per-wavelength absorptance, all four absorbers
  generation/              G(z) in the optical frame and the transport frame
  jv/                      every J-V curve, including the control runs
  mesh/                    mesh statistics and convergence data
scripts/
  full3d/                  the optical pipeline (stages 01-14)
  transport/               the device J-V runners
  figures/                 figure generation for the paper
manuscript/
  main.md, supplementary.md, figures/, figures_si/
REPRODUCE.md               this file
```

Simulation `.mph` model files are **not** included: they are 63–115 MB each,
exceed GitHub's file-size limit, and are byte-fragile across COMSOL versions.
They are rebuildable from the scripts, which is the supported path. Contact the
corresponding author if the binaries are needed.

---

## 2. Requirements

| Component | Version used | Notes |
|---|---|---|
| COMSOL Multiphysics | 6.2 (local), 6.3 (server) | needs Wave Optics + Semiconductor |
| Python | 3.8+ | 3.8 on the server, 3.10 locally |
| MPh | 1.2.4 / 1.3.1 | Python–COMSOL bridge |
| JPype1 | any recent | pulled in by MPh |
| NumPy, Matplotlib | 1.26 / 3.10 | figures only |

MPh locates COMSOL through `which comsol`, so putting the installation's `bin`
directory on `PATH` is the entire discovery step. **Do not move `.mph` files
between COMSOL versions** — rebuild from the scripts instead.

Hardware: the optical sweep is memory-bound, not core-bound. A single 300 nm
band-0 solve peaks near 85 GB. The full four-absorber sweep took ~20 h on a
96-core / 251 GB machine running two to six solves concurrently. The transport
runs are small: each J–V case takes 2–3 minutes at `cores=2` and fits in 7 GB.

---

## 3. Optical stage

```bash
cd full3d
source ./env.sh                      # puts COMSOL on PATH, sets MPh vars
export F3D_PROFILE=production F3D_TEXTURE=off F3D_ABSORBER=BaZrS3
./run_study.sh planar
```

`run_study.sh` runs, in order: geometry → materials → physics → per-band mesh
and solver → a periodicity check → three sweep passes (one per wavelength band,
with worker counts matched to each band's memory footprint) → a band-seam check
→ the photocurrent budget.

Repeat for `FASnI3`, `Cu2AgBiI6`, `Cs2AgBiBr6`, or use
`queue_planar_absorbers.sh` to run all of them back to back. All devices in
this study are planar; `F3D_TEXTURE` is left `off` throughout.

Then produce the generation profile:

```bash
python3 build/f3d_14_generation_profile.py planar
```

This writes G(z) twice: once in the optical model's coordinate frame and once
shifted +35 nm into the transport model's frame (the optical model truncates
the gold contact to 45 nm; the transport model keeps the full 80 nm). Use the
`_forTransport` file for device simulation.

**What to check before trusting the output.** Every run prints these; all must
pass.

| Check | Acceptance | Typical |
|---|---|---|
| Optical budget closure | \|error\| < 0.1 % | ±0.00 % |
| Per-wavelength energy residual | \|r\| < 2 % | worst −1.43 % |
| G(z) vs spectrum cross-check | \|Δ\| < 5 % | ≤ 0.05 % |
| Band-seam agreement | < 0.5 % | 0.020–0.096 % |

---

## 4. Transport stage

Device J–V uses a generic single-case runner, one fresh COMSOL session per case
so memory is released between runs:

```bash
python3 build_scripts/stage44_run_case.py <model.mph> <case_name> \
    <light:0|1> <rerun_std2:0|1> <heteromode:1|2> [key=value ...]
```

`key=value` sets COMSOL parameters. Three keys are special:
`VEND` (sweep end voltage), `VLIST` (explicit bias list, for dense
continuation), and `GZ` (repoint the generation-profile interpolation function
at a different file).

To reproduce the four devices of record on the refreshed optics:

```bash
./run_stage59.sh          # FASnI3, Cs2AgBiBr6, Cu2AgBiI6 (control + treatment)
./run_stage58.sh          # BaZrS3 (control + treatment + B_rad variant)
```

Extract metrics with:

```bash
python3 build_scripts/jv_metrics.py results/jv_<case>.csv
```

**Always run the regression fixture first.** Each driver script solves a
fixed-input reference case before the case under study. The fixture must
reproduce its recorded output exactly; if it does not, the model state is
wrong and nothing downstream is interpretable. See Trap 2.

---

## 5. Figures

```bash
python3 build_scripts/fig_ieee_main.py     # main text, 4 figures
python3 build_scripts/fig_ieee_si.py       # supplementary, 5 figures
python3 build_scripts/fig_ieee_extra.py    # band alignment (main) + G(z,lambda) map (SI)
python3 build_scripts/build_docx.py        # IEEE-typography .docx of both documents
```

Both read the result CSVs directly. Figures are drawn at IEEE printed size
(3.5 in single column, 7.16 in double) and exported as vector PDF plus 600 dpi
PNG. **Do not rescale them afterwards** — that is what produces unreadable axis
labels in print.

---

## 6. Traps

Each of these produces output that looks correct.

### Trap 1 — Floquet periodic boundaries need identical paired-face meshes

A free-tetrahedral mesh does not give the two faces of a periodic pair the same
surface mesh. COMSOL does not error; it interpolates, and the answer moves with
every remesh. Measured here at 700 nm: absorber absorptance 0.719 / 0.663 /
0.463 across meshes differing by 2.4 % in element count — a 36 % swing.

Fix: free-triangular mesh on x = 0 → copy face onto x = L → free-triangular on
y = 0 → copy onto y = L → tetrahedral fill. Order matters (the x and y faces
share the cell's vertical edges) and failure is silent. The implementation is
`full3d/f3d_mesh.py`, shared by the mesh and convergence stages so they cannot
drift apart.

**The energy-conservation residual will not catch this.** It compares total
absorbed power to total incident flux and is blind to how the total is split
between layers — which is exactly what the photocurrent depends on. Use the
band-seam check or `f3d_dbg_periodicity.py` instead.

When verifying periodicity directly: compare **tangential** field components,
not |E| (the normal component sampled on a face is interpolated from whichever
side the evaluator picks, and reports a mismatch that is not real), and expect
the x and y pairs to look different because the incident wave is x-polarized.

### Trap 2 — build scripts and saved models disagree

`build_scripts/build_stage15_heterojunction.py` sets the HTL acceptor doping to
`1e19 cm^-3`. The saved model holds `1e18`. A later stage changed it and only
the model records that. Restoring parameters from the script instead of the model shifts BaZrS₃'s
fill factor from 0.34 to 0.38 — a silent, plausible-looking error.

**Read device parameters back from the `.mph`, never from the build script.**
Additionally, `models/BaZrS3_pilot_3d_work.mph` is left in its *CuO* HTL
configuration by stage 32, not Spiro — check before assuming.

### Trap 3 — Cu₂AgBiI₆ needs dense bias continuation

At 25 mV steps the solver lands on spurious S-shaped
negative-differential-resistance branches and reports FF = 4.13, PCE = 86.6 %.
A 1 mV grid removes them. The artifact is deterministic, not stochastic, so it
reproduces — which makes it easy to mistake for a result.

Related: this absorber's **V_oc is not grid-converged** (1.512 V on a mixed
1–25 mV grid, 1.379 V on a uniform 1 mV grid) because its pre-V_oc tail is
nearly flat. P_max, V_mpp and J_mpp agree to five significant figures, so quote
those. Any comparison involving V_oc must be made at matched grid.

### Trap 4 — AM1.5G quadrature

Two errors, both pure quadrature, together worth ~30 %:

1. Weight each solve wavelength by the irradiance **integrated over its bin**,
   not sampled at the bin centre times the bin width. AM1.5G contains narrow
   atmospheric absorption lines that bin-centre sampling misrepresents (≈ 10 %).
2. **Clamp the outer bin edges** to the grid endpoints. Otherwise the first and
   last bins extend half a bin beyond the data and integrate a wider range than
   the comparison route does (+23 % on a coarse grid).

Both were found only by comparing two independent routes to the same
photocurrent. Build that redundant check first.

### Trap 5 — the Au back-contact truncation is not universally harmless

The optical model truncates Au at 45 nm over a PEC, justified by the
12–17 nm NIR skin depth. Au's interband damping dips near 450–570 nm
(roughly doubling the skin depth), and any absorber transparent in that
window lets light reach the contact, where the PEC returns an unphysically
strong wave. For Cs₂AgBiBr₆ this inflated the ceiling by 4.3 % (measured:
R = 0.469 truncated vs 0.292 thick-Au at 510 nm). Caught only by
`build_scripts/tmm_crosscheck.py`, the identical-geometry transfer-matrix
verification; corrected via `build_scripts/stage60_cabb_au_correction.py`,
whose three validation gates must pass before its output is trusted. The
other three absorbers extinguish this window first (≤0.35 % effect).

### General rule

Every defect found in this project produced plausible output — correct shape,
sane magnitudes, good energy conservation. None announced itself. All were
found by computing the same physical quantity two independent ways, or by
running a control that had to reproduce a known number before a new one was
believed. **A single run that looks right is not evidence.** When running a
control, match the treatment in every respect except the one variable under
test — including solver and continuation settings, not just physics.

---

## 7. Mapping results to the paper

| Paper item | Produced by | Data |
|---|---|---|
| Table I, optical ceilings | `f3d_10_photocurrent.py` | `results/optical/` |
| Table II, device metrics | `run_stage58.sh`, `run_stage59.sh` | `results/jv/` |
| Fig. 1, optical constants | `fig_ieee_main.py` | `data/optical_constants/` |
| Fig. 2, absorptance + budget | `fig_ieee_main.py` | `results/optical/` |
| Fig. 3, generation profiles | `fig_ieee_main.py` | `results/generation/` |
| Fig. 4, J–V curves | `fig_ieee_main.py` | `results/jv/` |
| Figs. S1–S5 | `fig_ieee_si.py` | as labelled |
| Fig. S7, TMM verification | `tmm_crosscheck.py` | `results/optical/` |
| Cs₂AgBiBr₆ correction | `stage60_cabb_au_correction.py` | `*_au80corr*` files |

---

## 8. Known limitations

- Interfaces are defect-free; reported efficiencies are upper bounds. No
  literature interface-recombination data exists for these material pairs.
- TiO₂ and Spiro-OMeTAD are optically lossless (k = 0), so all front parasitic
  absorption is attributed to the FTO. TiO₂ genuinely absorbs below ≈ 390 nm.
- The thermal loop is closed only for Cs₂AgBiBr₆.
- Cu₂AgBiI₆'s optical file carries a sub-gap tail supplying 38.2 % of its
  photocurrent, of which a 0.908 mA cm⁻² segment is a flat-α construction
  artifact rather than a physical Urbach tail.
- BaZrS₃'s transport gap (1.88 eV, BSE optical) and its measured optical onset
  (1.94 eV) differ by 0.06 eV; this is disclosed, not reconciled.
