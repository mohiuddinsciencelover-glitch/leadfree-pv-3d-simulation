# Interface Band Offsets, Not Optical Collection, Limit Four Chemically Distinct Lead-Free Absorbers: A Full-Wave 3-D Opto-Electro-Thermal Study

**Md. Mohiuddin and Alamgir Kabir**

*Department of Physics, University of Dhaka, Dhaka 1000, Bangladesh.*
*Corresponding author: alamgir.kabir@du.ac.bd*

> **EDITORIAL NOTE — REMOVE BEFORE SUBMISSION.** Text marked
> `[FLAG-n: …]` identifies a statement whose supporting citation or number
> could not be machine-verified and requires manual confirmation. A companion
> audit is in `audit/CITATION_VERIFICATION.md`. Do not submit with flags in
> place.

---

## Abstract

Lead-free absorbers are the leading route to non-toxic halide-perovskite
photovoltaics, but their device-simulation literature is dominated by
one-dimensional, single-material optimizations that prescribe the optical
generation profile, fix poorly known parameters, and rarely disclose parameter
provenance — yielding projected efficiencies difficult to reconcile with
experiment. We report a unified three-dimensional opto-electro-thermal
finite-element study of four chemically distinct lead-free absorbers (BaZrS₃,
FASnI₃, Cs₂AgBiBr₆, Cu₂AgBiI₆) in a single fixed architecture, coupling
full-wave electromagnetic optics to drift–diffusion transport, with every
fixed parameter literature-sourced and provenance-graded and every uncertain
parameter swept. Solving Maxwell's equations on the real multilayer stack
rather than assuming Beer–Lambert absorption changes the optical current
ceilings by −16 % to +23 % relative to prescribed-profile estimates, and in
one case the previously reported device photocurrent exceeded the corrected
ceiling — a physically impossible result that the full-wave treatment
resolves. Under defect-free interfaces no device is limited by optical
collection: the best collects 99.6 % of its optical ceiling. Each is instead
limited in voltage and fill factor by a band-offset cliff at a transport
interface. The four materials partition into two mechanistic classes,
electron-transport-layer conduction-band cliffs (FASnI₃, Cu₂AgBiI₆) and
hole-transport-layer valence-band cliffs (BaZrS₃, Cs₂AgBiBr₆). Closing the
thermal loop for Cs₂AgBiBr₆ gives a benign relative temperature coefficient of
≈ −0.12 % K⁻¹. Front-surface texturing recovers 3.02 mA cm⁻² of reflection but
delivers only 41 % of it to the absorber, the remainder being re-absorbed by
the textured transparent conductor. Transport-layer band engineering, not
further absorber optimization, is the operative design problem for this class.

**Index Terms** — Lead-free perovskite, photovoltaic cells, finite-element
methods, numerical simulation, band offset, opto-electro-thermal modeling,
light trapping.

---

## I. Introduction

Every halide perovskite solar cell that has crossed 26 % certified
power-conversion efficiency (PCE) is built on an absorber whose defining
component, divalent lead, is water-soluble and toxic — an unresolved liability
for the terawatt-scale, environmentally exposed deployment the technology is
meant to serve [1]. Regulatory pressure and life-cycle concerns have made the
replacement of lead the central materials problem of the field, and a
chemically diverse set of lead-free absorbers has emerged in response [2].
These candidates are not variations on a theme: they span fundamentally
different bonding, dimensionality, defect chemistry, and — crucially for
device design — band-edge energetics. That diversity is an opportunity, but it
also means lessons from optimizing one lead-free absorber rarely transfer to
another.

Four families frame the landscape. **Tin halide perovskites** such as FASnI₃
are the closest structural analogue to the lead compounds and the most advanced
in single-junction devices [3], reaching 14.51 % certified on 1 cm²
fullerene-free architectures [4] and 16.65 % in 2025 through 2D/3D
heterostructure engineering [5], though Sn²⁺→Sn⁴⁺ oxidation remains their
governing stability problem [6]. **Chalcogenide perovskites** such as BaZrS₃
replace halide with sulfide, offering exceptional thermal and moisture
stability [7]; their photovoltaic literature, however, remains overwhelmingly
computational, with SCAPS-1D optimizations projecting 22–34 % efficiencies
[8], [9] that far outrun nascent experimental demonstrations. **Halide double
perovskites** such as Cs₂AgBiBr₆ restore full inorganic stability, but wide
indirect gaps and sluggish transport cap experimental single-junction PCE near
6 % [10]–[12]. **Quaternary bismuth/silver iodides** such as Cu₂AgBiI₆ are
strongly absorbing, air-stable, wide-gap semiconductors attractive for tandem
top cells and indoor harvesting [13], [14], yet their experimental
efficiencies remain near 2 % [15], [16]. Across all four the pattern repeats:
promising absorber physics, modest real devices, and a simulation literature
whose optimism is hard to reconcile with experiment.

That reconciliation problem is largely methodological. The device-simulation
studies populating this literature are predominantly one-dimensional,
single-material optimizations that (i) prescribe the optical generation profile
from an assumed absorption coefficient rather than solving Maxwell's equations
for the real multilayer stack, (ii) fix critical and poorly known parameters —
electron affinity, carrier lifetime, interface recombination — at single
borrowed values and then optimize around them, (iii) treat the cell as
isothermal at 300 K, and (iv) rarely trace the origin of the inputs that
determine the answer. Under these conditions it is unsurprising that an
absorber capped near 6 % in the laboratory can be projected above 25 % on
paper.

This work addresses those gaps with a unified three-dimensional
opto-electro-thermal finite-element study of the four absorbers in a fixed
architecture. Full-wave electromagnetic optics feed a finite-volume
drift–diffusion transport model; every fixed material parameter is
literature-sourced with an explicit provenance status, and each genuinely
uncertain quantity is treated as a sensitivity sweep. Three results follow.
First, replacing prescribed generation profiles with full-wave optics shifts
the optical ceilings by −16 % to +23 %, and in one case removes a
thermodynamic inconsistency in previously reported device numbers. Second,
under defect-free interfaces no device is optically limited; each is limited by
a band-offset cliff, and the four partition into two mechanistic classes.
Third, front-surface texturing — the standard remedy for reflection loss —
delivers only 41 % of what it recovers, because the texture is made of the
absorbing transparent conductor.

---

## II. Computational Method

All devices were simulated in COMSOL Multiphysics (v6.2 locally, v6.3 on the
compute server) using a single self-consistent workflow coupling full-wave
electromagnetic optics to finite-volume drift–diffusion transport, with an
additional steady-state heat-transfer problem for Cs₂AgBiBr₆.

The governing principle for parameterization was to admit no unjustified point
assumptions. Every fixed material parameter is literature-sourced and carries
an explicit provenance status: **[EXP]** experimental, **[THEO]** computed
(level stated), **[SIM-LIT]** from published device simulations, **[DERIVED]**
computed by us from literature inputs through a stated parameter-free relation.
Quantities that are genuinely unknown or that conflict across the literature —
electron affinity χ, carrier lifetime τ, relative permittivity εᵣ, mobility µ,
doping — are **[SWEPT]** sensitivity axes. Full status-coded tables are in the
Supplementary Material (Tables S1–S2).

### A. Device architecture

A fixed stack is used throughout: glass / FTO (600 nm) / TiO₂ ETL (100 nm) /
absorber (300 nm) / Spiro-OMeTAD HTL (200 nm) / Au. The absorber is the only
layer that changes between devices, so all comparisons are on identical
optical, electrical, and numerical footing. The optical unit cell is
350 × 350 nm² with Floquet periodic boundaries on all four lateral faces, a
perfectly matched layer above, and a scattering boundary condition at the
illuminated plane.

### B. Optical model

The electromagnetic problem is solved in the frequency domain (COMSOL `ewfd`),
total-field formulation, for 61 wavelengths spanning 300–900 nm at 10 nm
resolution under AM1.5G (ASTM G173 global tilt) illumination [21]. Absorbed
power density is integrated per layer, giving a closed optical budget:
absorber + each parasitic layer + reflectance = incident.

Two aspects require care and are the origin of the ceiling changes reported
here. First, **Floquet periodic boundaries require the paired faces to carry
identical surface meshes.** A free-tetrahedral mesher does not produce this,
and COMSOL then interpolates across the mismatch without raising an error; the
computed absorptance wanders with every remesh. On this stack, absorber
absorptance at 700 nm took values 0.719 / 0.663 / 0.463 on meshes differing by
2.5 % in element count — a 36 % swing. The fix is to mesh one face of each pair
with a free-triangular operation and copy it onto the opposite face before the
tetrahedral fill. After the fix the same comparison gives 0.783103 vs 0.782888
(0.03 %). Critically, **the energy-conservation residual does not detect this
error**: it compares total absorbed power against total incident flux and is
blind to how that total is partitioned between layers, which is exactly what
the photocurrent depends on.

Second, meshes are banded by wavelength (300–390, 400–590, 600–900 nm) because
element count scales as λ⁻³; element size is set per material as λ/(n_eff·ppw)
with n_eff = |ñ|, subject to a skin-depth clamp and a floor of three elements
per layer thickness. Wavelengths at the band boundaries are solved on both
neighbouring meshes as a seam check.

The AM1.5G weighting integrates the irradiance over each wavelength bin rather
than sampling at bin centres — the standard spectrum contains narrow
atmospheric absorption lines that bin-centre sampling misrepresents — with
outer bin edges clamped to the grid endpoints.

### C. Electrical model

Transport is finite-volume drift–diffusion with Fermi–Dirac statistics,
Shockley–Read–Hall recombination, and a radiative term
R = B(np − nᵢ²) whose coefficient B is derived from the van
Roosbroeck–Shockley relation using the same optical constants that drive the
optical model, making it parameter-free rather than fitted. Heterojunctions are
treated in both quasi-Fermi-continuity and thermionic-emission modes; the two
agree to 0.2 %. The broadband generation profile G(z) from the optical stage is
laterally averaged and supplied to the transport model, which conserves
absorbed power per unit depth.

### D. Thermal model

For Cs₂AgBiBr₆ a steady-state heat-transfer problem is coupled to the optical
and electrical stages, with per-layer thermal conductivities all
literature-cited. Convective exchange is swept over h = 5–20 W m⁻² K⁻¹.

### E. Numerical procedure and validation

Every result carries two independent checks. The optical budget must close
(absorber + parasitics + reflectance = incident), and the depth integral of
G(z) must reproduce the photocurrent obtained independently from the
spectral integral of layer absorptance. These are different routes through the
same solve — a volume integral of a depth profile versus a spectral integral —
so agreement is meaningful. Across all four absorbers the budget closes to
±0.00 %, the worst per-wavelength energy residual is −1.43 %, the two
photocurrent routes agree within 0.05 %, and band seams agree to 0.020–0.096 %
(Fig. S2).

Device J–V curves use continuation in applied bias. For Cu₂AgBiI₆ a 25 mV grid
lands on spurious negative-differential-resistance branches; a 1 mV grid
removes them, and only the dense result is quoted (Section III-E).

---

## III. Results

### A. Full-wave optics changes the current ceilings

Fig. 1 shows the optical constants and Fig. 2 the resulting absorptance,
reflectance, and closed loss budget. Table I compares the optical current
ceiling — the photocurrent at 100 % collection — against the previous
prescribed-profile estimates.

**TABLE I. Optical current ceilings (mA cm⁻², AM1.5G, 100 % collection).**

| Absorber | Previous | This work | Change |
|---|---:|---:|---:|
| FASnI₃ | 18.27 | **20.450** | +11.9 % |
| Cu₂AgBiI₆ | 13.91 | **15.083** | +8.4 % |
| Cs₂AgBiBr₆ | 2.07 | **2.546** | +23.0 % |
| BaZrS₃ | 12.29 | **10.306** | −16.1 % |

Three of the four ceilings rise, principally because the transparent conductor
is now described by measured dispersion rather than a flat placeholder
extinction coefficient. BaZrS₃ falls, for a different and more consequential
reason: its optical constants were previously a Kramers–Kronig reconstruction
of a *computed* dielectric function that was zero-padded at 690 nm — inside its
own absorption range — whereas this work uses the measured ellipsometric
dielectric function [FLAG-1: Nishigaki et al., *Solar RRL* **4**, 1900555
(2020); verify volume/article number and that Table S2 is the Tauc–Lorentz
parameter table]. The measured data has markedly weaker near-edge absorption
and an onset at 639 nm (Fig. S1).

The consequence is material. The previously reported BaZrS₃ device photocurrent
of 11.85 mA cm⁻² **exceeds the corrected optical ceiling of 10.306 mA cm⁻²**,
which is impossible: the transport model was being supplied generation the
measured optics say does not occur. Section III-B resolves this.

The loss budget (Fig. 2c) shows the parasitic cost of the transparent
conductor is first-order for every absorber, ranging from 7.2 mA cm⁻² (FASnI₃)
to 10.0 mA cm⁻² (Cs₂AgBiBr₆) — in the weakly absorbing double perovskite the
contact absorbs four times more photocurrent than the absorber does.

### B. Devices of record

Every device was re-solved on the corrected generation profiles. Each re-run
was preceded by a control on the *previous* profile that had to reproduce the
published base case before the new result was accepted; all four controls
reproduced their targets exactly. Table II gives the outcome.

**TABLE II. Device metrics before and after the full-wave optical correction.**

| Absorber | J_sc (mA cm⁻²) | V_oc (V) | FF | PCE (%) | Collection |
|---|---:|---:|---:|---:|---:|
| FASnI₃ | 14.740 → **15.811** | 0.987 → 0.988 | 0.517 → 0.509 | 7.52 → **7.95** | 80.7 → 77.3 % |
| Cu₂AgBiI₆ | 13.856 → **15.017** | 1.379 → 1.384 | 0.519 → 0.518 | 9.91 → **10.76** | 99.6 → 99.6 % |
| BaZrS₃ | 11.846 → **9.883** | 1.341 → 1.337 | 0.340 → 0.340 | 5.40 → **4.48** | 96.4 → 95.9 % |
| Cs₂AgBiBr₆ | 2.010 → **2.473** | 1.710 → 1.766 | 0.287 → 0.280 | 0.98 → **1.22** | 97.3 → 97.1 % |

*Cu₂AgBiI₆ quoted on a matched 1 mV continuation grid (Section III-E).*

The BaZrS₃ inconsistency is resolved: 9.883 mA cm⁻² now sits below its 10.306
ceiling. Collection efficiency (95.9 %) and fill factor (0.340) are essentially
unchanged, so the entire loss is optical — a corrected input, not a changed
model.

**No device is limited by optical collection.** Cu₂AgBiI₆ collects 99.6 % of
its ceiling, Cs₂AgBiBr₆ 97.1 %, BaZrS₃ 95.9 %. Each is instead limited in
voltage and fill factor.

The one absorber whose collection *changes* is instructive. FASnI₃'s optical
ceiling rose 11.9 % but its photocurrent rose only 7.3 %, because collection
fell from 80.7 % to 77.3 %: the corrected optics front-load generation toward
the illuminated face, and FASnI₃ collects that less efficiently than the
flatter previous profile (Fig. 3). Cs₂AgBiBr₆, absorbing weakly and generating
almost uniformly, passes its full +23 % optical gain through to the device.
Whether an optical improvement reaches the terminals therefore depends on where
in the depth it deposits carriers — a distinction invisible to a
prescribed-profile model.

### C. Two classes of interface cliff

The limiting mechanism in every device is a band-offset cliff at a transport
interface, and the four materials partition into two classes. FASnI₃ and
Cu₂AgBiI₆ are limited by a **conduction-band cliff at the TiO₂ electron
contact** (0.79–0.99 eV for Cu₂AgBiI₆), which permits interfacial
recombination and caps fill factor. BaZrS₃ and Cs₂AgBiBr₆ are limited by a
**valence-band cliff at the Spiro-OMeTAD hole contact** (0.93 eV for BaZrS₃),
which blocks forward hole injection, produces an S-shaped J–V characteristic
and collapses fill factor to 0.28–0.34. The classes are orthogonal to the
chemistry: one tin halide and one bismuth iodide fall in the first, one
chalcogenide and one double perovskite in the second.

### D. Two natures of the open-circuit voltage

An independent axis distinguishes how V_oc is set. For FASnI₃ the radiative
term dominates and V_oc is pinned near its radiative limit. For the bismuth
halides, bulk Shockley–Read–Hall recombination sets it.

BaZrS₃ belongs to neither category, and correcting this is a substantive change
to the previously reported mechanism. We recomputed its radiative coefficient
from the van Roosbroeck–Shockley relation using the measured optical constants
and found **B_rad = 5.37 × 10⁻¹² cm³ s⁻¹, some 435× smaller** than the value in
use. Re-solving the device with the corrected coefficient moves V_oc by
**3 mV** (Fig. S5). BaZrS₃'s V_oc is therefore *not* at its radiative bound, as
previously stated; it is set by dark current through the Spiro injection
barrier. We further note that the previously used coefficient was internally
inconsistent — the van Roosbroeck–Shockley integral had been taken from
1.75 eV while nᵢ² was constructed from a 1.88 eV gap — making it ≈ 12× too
large even on its own optical data. Because the device is insensitive to it,
this does not affect any reported performance number, but the provenance
required correction.

### E. Numerical fidelity and disclosures

Three caveats must be stated explicitly.

**Cu₂AgBiI₆ sub-gap absorption.** 38.2 % of this absorber's photocurrent
(5.77 mA cm⁻²) originates below its 2.06 eV Tauc gap (Fig. S3). This is not an
artifact of the electromagnetic solve: the optical file is constructed from
tabulated ellipsometry above 2.0 eV and a photothermal-deflection tail shape
below it, zeroed under 1.40 eV [FLAG-2: verify the sub-gap tail construction
against Sansom et al. [13] and Kamppinen et al. [18]; confirm the anchoring
energy]. Consequently the ratio of photocurrent to the detailed-balance ceiling
at 2.06 eV reads 114 %, which is meaningless; we therefore report the
above-gap/sub-gap split rather than a ceiling fraction. Within that sub-gap
current, 0.908 mA cm⁻² (6.0 % of the total) arises from a segment where the
absorption coefficient stops decaying and sits flat at ≈ 2.7 × 10³ cm⁻¹ for
130 nm before stepping to zero — a construction artifact rather than a physical
Urbach tail. An optical ceiling credits all of these carriers at 100 %
collection, which is optimistic for tail states.

**Cu₂AgBiI₆ open-circuit voltage is not grid-converged.** The same model on a
mixed 1–25 mV continuation grid gives V_oc = 1.512 V and on a uniform 1 mV grid
1.379 V — a 133 mV spread. Maximum power, V_mpp and J_mpp are identical to five
significant figures (9.9126 mW cm⁻², 0.786 V, 12.612 mA cm⁻²), so PCE is
unaffected (Fig. S4). The cause is physical: the ETL cliff makes the pre-V_oc
tail nearly flat, so a 0.08 mA cm⁻² numerical difference moves the zero
crossing enormously. V_oc is poorly conditioned for this absorber and should be
quoted with this caveat; P_max-derived metrics are robust.

**Lossless transport layers.** TiO₂ and Spiro-OMeTAD are modeled with real-only
refractive indices (k = 0), so their budget entries are exactly zero and all
front parasitic absorption is attributed to the FTO. TiO₂ genuinely absorbs
below ≈ 390 nm, so UV generation in the absorber is slightly overestimated.
This treatment is identical across all four devices, so comparisons are
unaffected.

### F. Front-surface texturing delivers only part of what it recovers

Because reflection is the largest single loss for three of the four absorbers
(Fig. 2c), we tested the standard remedy on FASnI₃: a periodic front-surface
nanocone texture, identical stack otherwise. The texture raises the optical
ceiling from 20.450 to 21.679 mA cm⁻², a **+6.01 %** gain.

The headline, however, is not the gain but where the light goes (Fig. 5). The
texture reduces reflection by 3.024 mA cm⁻², but **only 1.229 mA cm⁻² (41 %)
reaches the absorber; 1.791 mA cm⁻² (59 %) is re-absorbed by the FTO**, because
the cone is made of FTO and adds ≈ 58 nm of equivalent conductor thickness.
The accounting closes exactly. This 41/59 split was identical in an earlier
iteration of the study using different absorber optical constants — with the
absorber's extinction coefficient differing by up to 5.8× — so it is structural
rather than an artifact of any one input. A non-absorbing texture (textured
glass, or a MgF₂/SiO₂ nanocone on flat FTO) would capture the full
3.02 mA cm⁻² and take the gain to roughly **+15 %**: a testable prediction that
the same pipeline evaluates by changing one material assignment.

---

## IV. Discussion

Three design consequences follow.

**Transport-layer band engineering is the operative problem.** With defect-free
interfaces every device already collects 96–99.6 % of its available
photocurrent; further absorber optimization cannot address what limits them.
The cliff taxonomy identifies which contact to change for which material:
FASnI₃ and Cu₂AgBiI₆ need a shallower-affinity electron contact, BaZrS₃ and
Cs₂AgBiBr₆ a deeper-HOMO hole contact. For BaZrS₃ neither Spiro-OMeTAD nor CuO
provides both a deep HOMO (≈ 5.9 eV) and a high conduction-band minimum, which
is why that material's HTL selection remains unresolved.

**Optical improvements must be evaluated in depth, not in aggregate.** The
FASnI₃/Cs₂AgBiBr₆ contrast shows that identical fractional gains in absorbed
photons produce different device gains depending on where carriers are
generated. Any light-management claim benchmarked only on absorptance may
overstate its device benefit.

**Parasitic absorption in the transparent conductor is first-order and is
worsened by texturing it.** The 41/59 split is a general caution: texturing an
absorbing contact converts a reflection loss into a parasitic absorption loss
and recovers only part of the difference.

**Limitations.** Interfaces are defect-free, so reported efficiencies are upper
bounds; no literature interface-recombination data exists for these material
pairs, and an interface recombination velocity sweep is provided instead
(Table S3). Transport layers are optically lossless (Section III-E). The
thermal loop is closed only for Cs₂AgBiBr₆. Cu₂AgBiI₆'s V_oc carries the
convergence caveat of Section III-E, and its optical constants include a
sub-gap tail whose device consequences we do not model as distinct from
band-edge carriers.

---

## V. Conclusion

A unified full-wave three-dimensional opto-electro-thermal study of four
chemically distinct lead-free absorbers in a fixed architecture shows that none
is limited by optical collection under defect-free interfaces; each is limited
by a band-offset cliff at a transport interface, and the four partition into
electron-contact and hole-contact cliff classes. Solving Maxwell's equations
rather than prescribing generation changes the optical ceilings by −16 % to
+23 % and removes a case in which a reported device photocurrent exceeded its
own optical ceiling. Front-surface texturing recovers reflection but delivers
only 41 % of it to the absorber when the texture is made of the transparent
conductor. Transport-layer band engineering, not further absorber optimization,
is the operative next step for this class of materials.

---

## Data Availability

All simulation inputs, build scripts, result files, and figure-generation code
are available at **[GITHUB-URL-PLACEHOLDER]**, together with `REPRODUCE.md`,
which documents the full pipeline end to end. Optical constants, AM1.5G
reference spectrum, per-wavelength absorptance spectra, generation profiles
G(z), and all J–V curves are included, as are the control runs used to validate
each re-simulation.

## Acknowledgment

The authors thank the Department of Physics, University of Dhaka, for
computational resources.

---

## References

> **CITATION STATUS.** Entries marked ⚠ were incomplete in the source
> bibliography (missing authors, journal, year, volume, or pages) and have been
> reconstructed or must be completed manually before submission. See
> `audit/CITATION_VERIFICATION.md`.

[1] ⚠ *Best Research-Cell Efficiency Chart*, National Renewable Energy
Laboratory. [Online]. Available: https://www.nrel.gov/pv/cell-efficiency.html
— **verify accession date; source list gave "NLR", likely a typo for NREL.**

[2] K. Prakash, I. Ahmed, and S. M. Mobin, "Strategic development of stable and
efficient lead-free perovskite solar cells," *Commun. Mater.*, vol. 7, no. 1,
p. 144, 2026.

[3] ⚠ "Smooth and compact FASnI₃ films for lead-free perovskite solar cells with
over 14 % efficiency." — **authors, journal, year, volume missing.**

[4] T. Li *et al.*, "Centimetre-scale fullerene-free tin-based perovskite solar
cells with a 14.51 % certified efficiency," *Nat. Energy*, vol. 11, no. 2,
pp. 219–229, 2026.

[5] D. He *et al.*, "Homogeneous 2D/3D heterostructured tin halide perovskite
photovoltaics," *Nat. Nanotechnol.*, vol. 20, no. 6, pp. 779–786, 2025.

[6] S. Yang, W. Fu, Z. Zhang, H. Chen, and C.-Z. Li, "Recent advances in
perovskite solar cells: Efficiency, stability and lead-free perovskite,"
*J. Mater. Chem. A*, vol. 5, no. 23, 2017. — ⚠ **page range missing.**

[7] ⚠ M. Kumar, A. Singh, S. K. Gill, and S. Bhattacharya, "Optoelectronic
properties of chalcogenide perovskites by many-body perturbation theory,"
*J. Phys. Chem. Lett.*, vol. 12, p. 5301, 2021. — **source list gave a variant
title; confirm which paper is intended.**

[8] A. Sowayan *et al.*, "Computational simulation and designing of highly
efficient chalcogenide BaZrS₃-based perovskite solar cells utilizing hole and
electron transport materials using SCAPS," *J. Phys. Chem. Solids*, vol. 207,
p. 112956, 2025.

[9] M. Guo *et al.*, "Device simulation of chalcogenide perovskite BaZrS₃ solar
cells with different structures," *Mater. Today Commun.*, vol. 46, p. 112686,
2025.

[10] ⚠ Zhang *et al.*, "[Hydrogenated Cs₂AgBiBr₆ double perovskite solar cell,
≈ 6.4 %]," 2022. — **incomplete: authors, title, journal all required.**

[11] J. Li, J. Duan, X. Yang, Y. Duan, P. Yang, and Q. Tang, "Review on recent
progress of lead-free halide perovskites in optoelectronic applications,"
*Nano Energy*, vol. 80, 2021. — ⚠ **article number missing.**

[12] M. S. Moed, A. A. Siddiquee, and M. T. B. Kashem, "Three-dimensional
optical-electrical simulation of Cs₂AgBiBr₆ double perovskite solar cells,"
2026. — ⚠ **journal missing.**

[13] H. C. Sansom *et al.*, "Highly absorbing lead-free semiconductor Cu₂AgBiI₆
for photovoltaic applications from the quaternary CuI–AgI–BiI₃ phase space,"
*J. Am. Chem. Soc.*, vol. 143, no. 10, pp. 3983–3992, 2021.

[14] T. Moon, "Rudorffite silver-bismuth iodides: Emerging eco-friendly
wide-bandgap absorbers for indoor photovoltaics," *Small*, vol. 21, no. 52,
p. e10252, 2025.

[15] M. A. Islam, S. Kato, N. Kishi, and T. Soga, "Enhanced surface morphology
and photovoltaic properties of a new class of material copper silver bismuth
iodide solar cell," *J. Mater. Res. Technol.*, vol. 25, pp. 4171–4186, 2023.

[16] A. Kamppinen, H. Palonen, and K. Miettunen, "Self-heating of planar
perovskite solar cells depending on active material properties," *ACS Appl.
Energy Mater.*, vol. 7, no. 10, pp. 4324–4334, 2024.

[17] P. Saxena and N. E. Gorji, "COMSOL simulation of heat distribution in
perovskite solar cells: Coupled optical–electrical–thermal 3-D analysis,"
*IEEE J. Photovolt.*, vol. 9, no. 6, pp. 1693–1698, 2019.

[18] ⚠ A. Kamppinen *et al.*, "Spectroscopic ellipsometry characterization and
radiative limit modeling of bismuth-based perovskite-inspired absorbers for
indoor photovoltaics," *Adv. Opt. Mater.*, 2026. — **volume, article number
required; this reference supplies the Cu₂AgBiI₆ optical constants and must be
complete.**

[19] M. Bahrami, M. Eskandari, and D. Fathi, "Thermal analysis of a plasmonic
perovskite solar cell: Using coupled opto-electro-thermal (OET) modeling,"
*Int. J. Energy Res.*, vol. 2024, no. 1, p. 3921832, 2024.

[20] R. Suldozi and M. Razaghi, "Investigation of perovskite solar cell
temperature-dependent performance: A coupled opto-electro-thermal modeling
approach," *Sci. Rep.*, vol. 16, no. 1, p. 19710, 2026.

[21] ⚠ *Standard Tables for Reference Solar Spectral Irradiances: Direct Normal
and Hemispherical on 37° Tilted Surface*, ASTM Standard G173-03. — **add ASTM
International, West Conshohocken, PA, and year.**

[22] Z. Yuan *et al.*, "Assessing carrier mobility, dopability, and defect
tolerance in the chalcogenide perovskite BaZrS₃," *PRX Energy*, vol. 3, no. 3,
p. 033008, 2024.

[23] ⚠ H. I. Eya and N. Y. Dzade, "Density functional theory insights into the
structural, electronic, optical, surface, and band alignment properties of
BaZrS₃ chalcogenide perovskite for photovoltaics." — **journal, year, volume
missing.**

[24] K. Ghimire, D. Zhao, Y. Yan, and N. J. Podraza, "Optical response of mixed
methylammonium lead iodide and formamidinium tin iodide perovskite thin films,"
*AIP Adv.*, vol. 7, no. 7, p. 075108, 2017.

[25] ⚠ L. Schade *et al.*, "Structural and optical properties of Cs₂AgBiBr₆
double perovskite." — **journal, year, volume missing.**

[26] J. DeVore, "Refractive indices of rutile and sphalerite," *J. Opt. Soc.
Am.*, vol. 41, pp. 416–419, 1951.

[27] K. M. McPeak *et al.*, "Plasmonic films can easily be better: Rules and
recipes," *ACS Photonics*, vol. 2, no. 3, pp. 326–333, 2015.

[28] K. Ungeheuer, K. W. Marszalek, M. Mitura-Nowak, and A. Rydosz,
"Spectroscopic ellipsometry modelling of Cr⁺ implanted copper oxide thin
films," *Sci. Rep.*, vol. 13, no. 1, p. 22116, 2023.

[29] Md. B. Rahman, Noor-E-Ashrafi, Md. H. Miah, M. U. Khandaker, and M. A.
Islam, "Selection of a compatible electron transport layer and hole transport
layer for the mixed perovskite FA₀.₈₅Cs₀.₁₅Pb(I₀.₈₅Br₀.₁₅)₃," *RSC Adv.*,
vol. 13, no. 25, pp. 17130–17142, 2023.

[30] A. Usman and T. Bovornratanaraks, "Modeling and optimization of modified
TiO₂ with aluminum and magnesium as ETL in MAPbI₃ perovskite solar cells:
SCAPS 1D frameworks," *ACS Omega*, vol. 9, no. 38, pp. 39663–39672, 2024.

[31] ⚠ W. van Roosbroeck and W. Shockley, "Photon-radiative recombination of
electrons and holes in germanium," *Phys. Rev.*, vol. 94, no. 6, pp. 1558–1560,
1954. — **reconstructed from a title-only entry; verify.**

[32] ⚠ Y. Li *et al.*, "Dynamic local order and ultralow thermal conductivity
of Cs₂AgBiBr₆." — **journal, year, volume missing.**

[33] J. Mun, S. W. Kim, R. Kato, I. Hatta, S. H. Lee, and K. H. Kang,
"Measurement of the thermal conductivity of TiO₂ thin films by using the
thermo-reflectance method," *Thermochim. Acta*, vol. 455, no. 1, pp. 55–59,
2007.

[34] N. Oka *et al.*, "Thermophysical properties of SnO₂-based transparent
conductive films," *J. Mater. Res.*, vol. 29, no. 15, pp. 1579–1584, 2014.

[35] C. Y. Ho, R. W. Powell, and P. E. Liley, "Thermal conductivity of the
elements," *J. Phys. Chem. Ref. Data*, vol. 1, no. 2, pp. 279–421, 1972.

[36] X. Wang, K. D. Parrish, J. A. Malen, and P. K. L. Chan, "Modifying the
thermal conductivity of small molecule organic semiconductor thin films with
metal nanoparticles," *Sci. Rep.*, vol. 5, no. 1, p. 16095, 2015.

[37] ⚠ Y. Pai *et al.*, "Solution processable direct bandgap copper-silver-
bismuth iodide photovoltaics: Compositional control of dimensionality and
optoelectronic properties," *Adv. Energy Mater.*, 2022. — **volume, article
number missing.**

[38] T. Minemoto *et al.*, "Theoretical analysis of the effect of conduction
band offset of window/CIS layers on performance of CIS solar cells using device
simulation," *Sol. Energy Mater. Sol. Cells*, vol. 67, no. 1, pp. 83–88, 2001.

[39] J. Zheng, C. Lin, C. Lin, G. Hautier, R. Guo, and B. Huang, "Unravelling
ultralow thermal conductivity in perovskite Cs₂AgBiBr₆," *npj Comput. Mater.*,
vol. 10, no. 1, p. 30, 2024.

[40] ⚠ "Band gaps of the lead-free halide double perovskites Cs₂BiAgCl₆ and
Cs₂BiAgBr₆ from theory and experiment," *J. Phys. Chem. Lett.* — **authors,
year, volume, pages all missing; likely Filip et al., 2016.**

[41] A. A. El-Naggar *et al.*, "Numerical simulation based performance
enhancement approach for an inorganic BaZrS₃/CuO heterojunction solar cell,"
*Sci. Rep.*, vol. 14, p. 7614, 2024.

[42] K. Ungeheuer *et al.*, "DFT electronic structure investigation of chromium
ion-implanted cupric oxide thin films dedicated for photovoltaic absorber
layers," *Sci. Rep.*, vol. 14, no. 1, p. 19830, 2024.

[43] **NEW — required by this work.** ⚠ K. Nishigaki *et al.*, "Extraordinary
strong band-edge absorption in distorted chalcogenide perovskites,"
*Solar RRL*, vol. 4, p. 1900555, 2020. — **verify authors and title; supplies
the measured BaZrS₃ dielectric function (Table S2).**

[44] **NEW — required by this work.** ⚠ K. von Rottkay and M. Rubin, "Optical
indices of pyrolytic tin-oxide glass," *Mater. Res. Soc. Symp. Proc.*,
vol. 426, p. 449, 1996 (LBNL-38586). — **verify; supplies the FTO dispersion.**
