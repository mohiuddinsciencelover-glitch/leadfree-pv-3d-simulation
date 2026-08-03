# Supplementary Material

## Interface Band Offsets, Not Optical Collection, Limit Four Chemically Distinct Lead-Free Absorbers: A Full-Wave 3-D Opto-Electro-Thermal Study

**Md. Mohiuddin and Alamgir Kabir**
*Department of Physics, University of Dhaka, Dhaka 1000, Bangladesh*

> **EDITORIAL NOTE — REMOVE BEFORE SUBMISSION.** `[FLAG-n: …]` marks a
> statement whose supporting citation or value requires manual confirmation.
> See `audit/CITATION_VERIFICATION.md`.

---

## S1. Supplementary Figures

**Fig. S1. Optical-constant replacements.** Extinction coefficient *k* of
(a) FASnI₃ and (b) BaZrS₃, comparing the data used previously with the data
used here. (a) The previous FASnI₃ file was assembled by splicing two
pixel-traced figures from the same publication [24] at 1.70 eV. Across that
5 nm join *k* falls 0.4263 → 0.0792, a 5.8× discontinuity, after which it sits
nearly flat to 850 nm — behaviour no direct-gap absorber exhibits. It is
replaced here by the tabulated dielectric function from the same paper's
supplementary information (695 points, point-by-point inversion of measured
ellipsometry). (b) The previous BaZrS₃ file was a Kramers–Kronig
reconstruction of a *computed* ε₂ that was hard-zeroed at 690 nm, cutting from
α = 2.6 × 10⁴ cm⁻¹ directly to zero while the stated band edge lay at 708 nm.
It is replaced by the measured ellipsometric dielectric function [43].

**Fig. S2. Validation.** (a) Per-wavelength energy-budget residual for all four
absorbers against the ±2 % acceptance band; the worst value across 244 solves
is −1.43 %, at 300 nm, the finest mesh in the study. (b) Band-seam agreement:
wavelengths at the 400 nm and 600 nm band boundaries were solved on both
neighbouring meshes, which are generated independently. Agreement is
0.020–0.096 %. This is the check that detects the Floquet periodic-mesh defect
described in Section S3; the energy residual does not.

**Fig. S3. Cu₂AgBiI₆ sub-gap absorption.** (a) Absorber absorptance with the
2.06 eV Tauc gap marked; the shaded region is sub-gap. (b) Decomposition of the
15.083 mA cm⁻² optical ceiling by spectral region. 61.8 % lies above the Tauc
gap; 28.9 % is an Urbach-like tail with characteristic energy ≈ 88 meV; 3.3 % a
weak tail; and 6.0 % (0.908 mA cm⁻²) arises where α stops decaying and sits
flat at ≈ 2.7 × 10³ cm⁻¹ for 130 nm before stepping to zero at 886 nm — a
construction artifact of the optical file rather than a physical tail.

**Fig. S4. Cu₂AgBiI₆ open-circuit voltage is not grid-converged.** (a) J–V on a
mixed 1–25 mV continuation grid versus a uniform 1 mV grid. The curves are
identical through the maximum power point (P_max = 9.9126 mW cm⁻²,
V_mpp = 0.786 V, J_mpp = 12.612 mA cm⁻², to five significant figures).
(b) Magnified pre-V_oc tail: the curves diverge only beyond ≈ 1.3 V where
J < 0.2 mA cm⁻² and the characteristic is nearly flat, so a 0.08 mA cm⁻²
difference moves the zero crossing from 1.512 V to 1.379 V.

**Fig. S5. BaZrS₃ radiative coefficient.** (a) van Roosbroeck–Shockley
B_rad as a function of the lower integration limit, for the previous
(Kramers–Kronig of computed ε₂) and present (measured ellipsometry) optical
constants. The previously used value, 2.335 × 10⁻⁹ cm³ s⁻¹, corresponds to the
old optics integrated from 1.75 eV, whereas nᵢ² in the same model is built from
E_g = 1.88 eV — an internal inconsistency making it ≈ 12× too large even on its
own data. Evaluated consistently at 1.88 eV on the measured optics,
B_rad = 5.37 × 10⁻¹² cm³ s⁻¹. (b) Device J–V with both coefficients: a 435×
change moves V_oc by 3 mV, establishing that BaZrS₃'s V_oc is not
radiatively limited.

---

## S2. Device architecture and parameter provenance

The stack is fixed for all four devices: glass / FTO (600 nm) / TiO₂ (100 nm) /
absorber (300 nm) / Spiro-OMeTAD (200 nm) / Au. The optical unit cell is
350 × 350 nm² with Floquet periodicity on all lateral faces.

**Provenance codes.** **[EXP]** experimental; **[THEO]** computed, level
stated; **[SIM-LIT]** from published device simulations; **[DERIVED]** computed
here from literature inputs by a stated parameter-free relation; **[SWEPT]**
treated as a sensitivity axis rather than a fixed value.

### TABLE S1. Absorber parameters

| Quantity | BaZrS₃ | FASnI₃ | Cs₂AgBiBr₆ | Cu₂AgBiI₆ | Status |
|---|---|---|---|---|---|
| E_g (eV) | 1.88 [7] | 1.41 | 2.32 [FLAG-3] | 2.06 [13] | [THEO]/[EXP] |
| χ (eV) | 4.1 [41] | 3.50 | 4.0 | 3.22 | **[SWEPT]** |
| m_e*/m_0 | 0.3 | — | 0.33 | — | [THEO] |
| m_h*/m_0 | 0.9 | — | 0.84 | — | [THEO] |
| τ_SRH | 1 ns [EXP] / 33 ns [THEO] [22] | 43 / 123 ns | 13.7 ns / 1 µs | 33 / 3.3 ns | **[SWEPT]** |
| ε_r | — | 8.2 / 6 / 10 | 5.8 / 3.54 | 6.3 / 12 | **[SWEPT]** |
| µ (cm² V⁻¹ s⁻¹) | — | 67 / 22 | 0.57 / 6 | 1.7 / 5.1 | **[SWEPT]** |
| Doping (cm⁻³) | N_d 4.4×10¹⁰ | — | — | N_a 1×10¹² | [SWEPT] |
| B_rad (cm³ s⁻¹) | **5.37×10⁻¹²** | 7.99×10⁻⁸ | 3.19×10⁻¹² | — | **[DERIVED]** |
| Optical constants | measured ellipsometry [43] | tabulated SI ε [24] | σ-route [FLAG-4] | ellipsometry + PDS tail [18] | [EXP] |

**Notes.** BaZrS₃'s E_g = 1.88 eV is the BSE optical gap [7]; the measured
optical data [43] gives an absorption onset at 1.94 eV, a 0.06 eV difference
that is disclosed rather than reconciled. Several distinct BaZrS₃ gap values
circulate (HSE06 1.81 eV, BSE optical 1.88 eV, GW 2.10 eV, measured onset
≈ 1.9–1.94 eV) and must not be conflated [FLAG-5].
Cs₂AgBiBr₆'s k was derived through the conductivity route after the source's
absorption-coefficient panel was found to be internally inconsistent by a
factor of 2π with its own σ and ε₂ panels [FLAG-4: independently confirm this
2π discrepancy in the cited figure before publication].
BaZrS₃'s B_rad is corrected here from 2.335 × 10⁻⁹ (see Fig. S5).

### TABLE S2. Transport-layer and contact parameters

| Quantity | TiO₂ (ETL) | Spiro-OMeTAD (HTL) | Source |
|---|---|---|---|
| E_g (eV) | 3.2 | 2.9 | [30], [29] |
| χ (eV) | 4.15 | 2.15 | [30], [29] |
| ε_r | — | 3 | [29] |
| µ_n, µ_p (cm² V⁻¹ s⁻¹) | — | 1×10⁻⁴ | [29] |
| N_c, N_v (cm⁻³) | 2.2×10¹⁸, 1×10¹⁹ | 2.2×10¹⁸, 2.2×10¹⁸ | [29], [30] |
| Doping (cm⁻³) | N_d 5×10¹⁷ | N_a 1×10¹⁸ | [29] |
| Optical | Sellmeier, k = 0 [26] | n = 1.75, k = 0 | see S5 |
| FTO work function (eV) | 4.6 | — | [29] |

**Disclosed disagreements.** Two literature conflicts are carried openly rather
than silently resolved. Spiro-OMeTAD band gap: 2.9 eV [29] versus 3.2 eV
[FLAG-6: Tiwari et al. 2022 — add to reference list if retained]. Spiro N_v:
2.2 × 10¹⁸ [29] versus 1.8 × 10¹⁹ [FLAG-6]. We use [29] throughout. A third
reported value, a Spiro hole mobility of 2 × 10⁴ cm² V⁻¹ s⁻¹, is rejected as a
transcription error — it is roughly ten orders of magnitude above the
well-established ≈ 10⁻⁴ cm² V⁻¹ s⁻¹ for this material [FLAG-6].

**A reproducibility caution.** The HTL acceptor doping is 1 × 10¹⁸ cm⁻³ in the
saved model but 1 × 10¹⁹ cm⁻³ in the build script that nominally creates it; a
later stage changed the value and only the model file records it. Restoring
device parameters from the build script rather than the model yields
J_sc = 12.095 mA cm⁻² and FF = 0.381 for BaZrS₃ instead of 11.846 and 0.340.
Parameters must be read back from the saved model.

### TABLE S3. Sensitivity sweeps (BaZrS₃/Spiro, previous optics)

| Case | J_sc | V_oc | FF | PCE |
|---|---:|---:|---:|---:|
| χ = 4.1, τ = 1 ns (base) | 11.85 | 1.341 | 0.340 | 5.40 % |
| χ = 4.1, τ = 33 ns | 12.28 | — | — | — |
| Interface recombination S = 10²–10⁶ cm s⁻¹ | see S6 | | | |

No literature interface-recombination data exists for any of these material
pairs, so S is swept rather than assigned.

---

## S3. The Floquet periodic-mesh defect

Floquet periodic boundary conditions require the paired faces of the unit cell
to carry **identical surface meshes**. A free-tetrahedral mesher does not
produce this. COMSOL does not raise an error; it interpolates across the
mismatch, and the computed per-layer absorption depends on the particular mesh
realization.

Measured on this stack at 700 nm, absorber absorptance took the values

| Elements | A_absorber |
|---:|---:|
| 120 153 | 0.719 |
| 120 346 | 0.663 |
| 123 031 | 0.463 |

— a 36 % swing for a 2.5 % change in element count. The remedy is to mesh
x = 0 with a free-triangular operation, copy that mesh onto x = L, repeat for
y, and only then fill with tetrahedra; feature order matters because the x and
y faces share the cell's vertical edges. After the fix the same comparison
gives 0.783103 versus 0.782888 (0.03 %), and the energy budget closes to
0.03 % instead of 1.2 %.

**The energy-conservation residual does not detect this defect.** It compares
total absorbed power against total incident flux and is insensitive to how that
total is partitioned between layers — which is precisely what the photocurrent
depends on. Detection requires either a mesh-versus-mesh comparison or a
tangential-field equality check on the paired faces (which reaches 0.00000 %
after the fix). Two traps arise in the latter: compare the **tangential** field
components, not |E|, because the normal component sampled on a face is
interpolated from whichever side the evaluator picks; and expect the x and y
pairs to differ, because the incident wave is x-polarized.

---

## S4. Numerical procedure

**Wavelength banding.** Element count scales as λ⁻³, so meshes are generated
per band: 300–390, 400–590, 600–900 nm. Element size is λ/(n_eff · ppw) with
n_eff = |ñ|, subject to a skin-depth clamp and a floor of three elements across
any layer thickness. The wavelength-independent cap is applied only to air and
the perfectly matched layer, never to the absorber, so that resolution genuinely
varies with the local index.

**Two independent photocurrent routes.** The depth integral of G(z) and the
spectral integral of layer absorptance are computed separately and compared
every run. They share the solve but nothing else — a volume integral of a depth
profile versus a spectral integral of a per-layer quantity. Agreement across
the four absorbers is +0.05 %, +0.03 %, −0.04 %, +0.04 %.

**AM1.5G quadrature.** Irradiance is integrated over each wavelength bin rather
than sampled at bin centres, and the outer bin edges are clamped to the grid
endpoints. Bin-centre sampling biased the result by ≈ 10 % and unclamped edges
by a further +23 % on a coarse grid; both are quadrature errors rather than
physics, and both were exposed by the two-route comparison above.

**Bias continuation.** J–V curves use continuation in applied bias with
interface-type continuation on the heterojunctions. For Cu₂AgBiI₆ a 25 mV grid
converges onto spurious S-shaped negative-differential-resistance branches
reporting FF = 4.13 and PCE = 86.6 %; a 1 mV grid removes them. Only dense
results are quoted for that absorber. The artifact is reproducible rather than
stochastic.

### TABLE S4. Validation ledger

| Check | FASnI₃ | Cu₂AgBiI₆ | BaZrS₃ | Cs₂AgBiBr₆ |
|---|---:|---:|---:|---:|
| Optical budget closure | −0.00 % | +0.00 % | +0.00 % | +0.00 % |
| Worst energy residual | −1.36 % | −1.39 % | −1.43 % | −1.35 % |
| G(z) vs spectrum cross-check | +0.05 % | +0.03 % | +0.04 % | −0.04 % |
| Band seam, 400 nm | 0.070 % | 0.079 % | 0.075 % | 0.096 % |
| Band seam, 600 nm | 0.023 % | 0.020 % | 0.020 % | 0.000 % |
| Control reproduces published case | exact | exact | exact | exact |

---

## S5. Optical model limitations

**Lossless transport layers.** TiO₂ is modeled with a Sellmeier real index
[26] clamped below 400 nm (its 283 nm pole otherwise returns n = 5.58 at the
blue end of the grid), and Spiro-OMeTAD with a constant n = 1.75; both carry
k = 0. Their budget entries are therefore exactly zero and all front parasitic
absorption is attributed to the FTO. TiO₂ genuinely absorbs below its ≈ 390 nm
edge, so UV generation in the absorber is slightly overestimated. The treatment
is identical for all four devices, so relative comparisons are unaffected.

**FTO.** Previously modeled with a fabricated flat k = 0.02; here it uses
measured SnO₂:F dispersion [44].

**Gold contact.** Truncated to 45 nm in the optical model — more than three
skin depths at all wavelengths considered, and backed by a perfect electric
conductor — while the transport model retains the full 80 nm. The generation
profile is therefore shifted by 35 nm when handed to the transport stage, and
both frames are provided in the archive.

---

## S6. Interface recombination

No experimental interface-recombination velocity exists for any of these
absorber/transport-layer pairs. Rather than assign one, S is swept over
10², 10⁴ and 10⁶ cm s⁻¹ with all other parameters at their base values. The
reported efficiencies in the main text correspond to defect-free interfaces
(S = 0) and are therefore upper bounds.

---

## S7. Data and code availability

All inputs, scripts, results and figure code are archived at
**[GITHUB-URL-PLACEHOLDER]**. `REPRODUCE.md` documents the pipeline end to end,
including the four traps that cost significant time during development (the
periodic-mesh defect, the build-script/model parameter divergence, the
Cu₂AgBiI₆ continuation-grid artifact, and the two AM1.5G quadrature errors).
The archive contains optical constants, the AM1.5G reference spectrum,
per-wavelength absorptance for every absorber, generation profiles in both the
optical and transport coordinate frames, every J–V curve including the control
runs used to validate each re-simulation, and the mesh-convergence data.
