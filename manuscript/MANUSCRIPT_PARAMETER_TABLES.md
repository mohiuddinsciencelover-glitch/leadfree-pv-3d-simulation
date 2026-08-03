# Manuscript Parameter Tables — Complete Provenance Record
**Materials studied so far: BaZrS3 (device 1) and FASnI3 (device 2).**
Compiled 2026-07-19. Every value in this file is exactly what the COMSOL models used
(models/BaZrS3_pilot_3d_work.mph and models/FASnI3_pilot_3d.mph). Status codes:
**[EXP]** experimental literature · **[THEO]** computed literature (level stated) ·
**[SIM-LIT]** value used in published device simulations (upstream source not independently verified) ·
**[DERIVED]** computed by us from literature inputs via a stated parameter-free relation ·
**[PLACEHOLDER]** not literature-pinned — must be disclosed ·
**[SWEPT]** treated as sensitivity axis because sources conflict or value is uncertain.

---

## 1. Simulation conventions (both devices)

| Item | Value | Source / note |
|---|---|---|
| Spectrum | ASTM G173-03 global tilt; P_in = 1000.37 W/m² (actual integral of the standard, disclosed vs rounded 1000) | pvlib 0.15.2 `spectrum.get_reference_spectra("ASTM G173-03")`; file `AM15G_ASTM_G173_global.csv` |
| Temperature | 300 K uniform (all material models tied to T_dev) | standard test condition |
| Geometry | 3D unit cell 350×350 nm, periodic X/Y; Au 80 / HTL 200 / absorber 300 / TiO2 50 / FTO 600 / air 410 nm | fixed cross-family architecture (paper framing) |
| Optics | Full-wave EM (ewfd), per-λ incident amplitude from spectral bin power; λ grids 300–700 nm (BaZrS3) / 300–900 nm (FASnI3), 10 nm steps | scripts stage21/33/43 |
| Transport | Drift-diffusion (finite volume), Maxwell-Boltzmann statistics, ideal ohmic contacts (FTO work function NOT used — SCAPS-equivalent contact treatment, disclose) | |
| Heterojunctions | Both limits computed: thermionic emission ('2') and quasi-Fermi continuity ('1', SCAPS convention). BaZrS3/CuO: limits agree to 0.2% → interface-model-robust. FASnI3: QF mode used | |
| Recombination | SRH (τ swept, see per-material) + radiative R = B(np−ni²) with B **[DERIVED]** via van Roosbroeck–Shockley from each material's literature α(E), n(E) + its Nc, Nv, Eg. No Auger (no literature coefficients). No interface traps in baseline (no literature data; S-sweep shown for BaZrS3) | |
| Numerics | Doping+band-offset continuation ramp 1e-8→1 (COMSOL heterojunction_1d pattern); χ-continuation for stiff cases; forward bias = NEGATIVE Vapp on the top (n-side) contact, reported as +V | |
| Mesh | Mapped+swept, ~1 nm z-resolution at junctions, 3875 elements; independence ≤0.035% J-change at 1.5× refinement (checked on the most Debye-demanding configuration) | |

---

## 2. BaZrS3 absorber

| Parameter | Value used | Status | Source |
|---|---|---|---|
| Band gap Eg | 1.88 eV | [THEO, BSE@G0W0@PBE optical gap] | Kumar, Singh, Gill, Bhattacharya, *J. Phys. Chem. Lett.* 2021, 12, 5301 (arXiv:2103.17264). Matches experimental ellipsometry onset (~1.9 eV). Report alongside: HSE06 1.81 eV (Yuan 2024), G0W0 QP gap 2.10 eV, exciton binding 0.21 eV |
| Electron affinity χ | 4.10 eV, **[SWEPT] 3.9/4.0/4.1** | [SIM-LIT] | Sci. Rep. 2024 (PMC10982297) Table 1. Primary DFT source (ACS AEM 2023, 10.1021/acsaem.3c00103 SI Tables S2a/b) inaccessible after repeated attempts — state this in methods |
| Rel. permittivity ε_r | 79.4 | [THEO, PBE electronic+ionic; isotropic avg of εxx=82.10, εyy=70.67, εzz=85.46] | Yuan et al., *PRX Energy* 2024, 3, 033008 |
| Effective masses | me*=0.3, mh*=0.9 m0 | [THEO, HSE06-based] | Yuan 2024 |
| Nc, Nv (300 K) | 4.12e18 / 2.14e19 cm⁻³ | [DERIVED] closed-form 2(2πm*kT/h²)^1.5 from the masses above | standard formula |
| Mobilities μn/μp | 37 / 11 cm²/Vs | [THEO, phonon-limited BTE] | Yuan 2024 |
| Doping | n-type, Nd = 4.4e10 cm⁻³ ("optimized low-defect processing" value) | [THEO/EXP-informed] | Yuan 2024 + arXiv:2501.16561, arXiv:2505.16016. NOTE: the alternative "conventional high-T sulfurization" 1e19–1e20 cm⁻³ exceeds Nc → physically inconsistent with MB statistics; documented choice |
| τ_SRH | **[SWEPT] 1 ns / 33 ns** | 1 ns [EXP, TRPL single crystal] / 33 ns [THEO, S-interstitial capture] | Nielsen et al., *Adv. Opt. Mater.* 2025 (arXiv:2503.16180) / Yuan 2024. Nielsen's PLQY≈0.005% ⇒ the 1 ns decay is non-radiative-dominated (do NOT call it radiative) |
| Radiative B | 2.335e-9 cm³/s | [DERIVED, van Roosbroeck–Shockley] | from our KK α(E), n(E) + Nc,Nv,Eg above. Parameter-free; state the relation in methods |
| n(λ), k(λ) | `BaZrS3_nk_KK.csv` | [DERIVED: KK of digitized BSE ε₂, anchored] | ε₂: Kumar 2021 Fig. 3d (pixel-traced). KK (Maclaurin) with constant Δε₁=+3.95 (52% of anchor — DISCLOSE) calibrated to n=2.75 [THEO, ACS AEM 2023]. Validations: α≈1e5 cm⁻¹ above gap (matches ACS AEM 2023); k≡0 below 1.80 eV; 0.04 pixel-noise floor subtracted |
| Density ρ | 4.22 g/cm³ (present in model; unused — no heat physics) | — | confirmed literature value (handoff record) |
| Thermal κ, Cp | κ param 1.5 W/mK present but UNUSED; Cp not found in literature — heat-transfer physics not built | [GAP] | κ literature range 1.11–1.84 (3 studies); Cp genuinely absent — state as limitation |

## 3. FASnI3 absorber

| Parameter | Value used | Status | Source |
|---|---|---|---|
| Band gap Eg | 1.41 eV | [EXP, film] | Experimental value tabulated in Tao, Cao, Bobbert, *Sci. Rep.* 2017, 7, 14386. Consistent with the 1.40 eV absorption edge of the n,k source below. GW=1.27 eV (Mosconi via same paper) quoted as theoretical reference only — NOT used, to keep optics/transport self-consistent |
| Electron affinity χ | 3.50 eV, **[SWEPT] 3.5/3.75/4.0** | [EXP] base | 3.49–3.51 eV experimental CBM-vs-vacuum: *Nano-Micro Lett.* 2022 ("Heterogeneous FASnI3 Absorber..."). 4.0 eV [SIM-LIT]: PMC9316066 Table 1. Both literature → swept; this axis controls FF (see results) |
| Rel. permittivity ε_r | 8.2, **[SWEPT] 6/8.2/10** | [SIM-LIT], mid of [EXP] range | PMC9316066 Table 1; experimental range 6–10 (Stoumpos et al. 2013, via Srivastava & Pandey 2026 Table 7). Result: negligible sensitivity |
| Nc, Nv | 1e18 / 1e18 cm⁻³ | [SIM-LIT] | PMC9316066 Table 1 (their refs [19],[56],[57]) |
| Mobilities μn=μp | 67 cm²/Vs, sensitivity 22 | [EXP, FET; ambipolar — carrier-unresolved, DISCLOSE] | "High-Mobility and Bias-Stable FETs...", *ACS Energy Lett.* 2023 / 22: PMC9316066 |
| Doping | p-type, Na = 1.5e17 cm⁻³ | [EXP, Hall+PL, 10% SnF2-treated film] | *ACS Energy Lett.* 2023 (same paper). PMC9316066 uses 7e16 (same order) |
| τ_SRH | **[SWEPT] 43 / 123 ns** | [EXP, PL decay, SnF2/additive-treated films; trap-influenced effective lifetime — DISCLOSE] | *ACS Energy Lett.* 2023. Result: zero sensitivity (Voc radiative-pinned) |
| Radiative B | 7.99e-8 cm³/s | [DERIVED, VRS] | from the experimental n,k below + Nc,Nv,Eg above |
| n(λ), k(λ) | `FASnI3_nk_Ghimire2017.csv` | [EXP, spectroscopic ellipsometry, digitized] | Ghimire, Zhao, Yan, Podraza, *AIP Adv.* 7, 075108 (2017), CC-BY; pure-FASnI3 (1.00:0.00) series; Fig. 2 (full range) + Fig. 3A (onset zoom) spliced at 1.70 eV; achromatic-mask pixel tracing. Validations: α(1.40 eV)=4.2e3 vs paper's 4.0e3 cm⁻¹ edge criterion; ε₂ peak 5.86 @2.26 eV vs CP 2.21 eV; n(0.8 eV)=2.41 in exp. range 2.4–3.0. Their SI has TABULATED ε (doi 10.1063/1.4994211, bot-walled) — replace digitization if obtained. Small splice kink 1.70–1.77 eV (Fig 3A y-clip) — disclose |
| Thermal | none used (κ only qualitative in literature; Cp figure-only) | [GAP] | |

## 3b. Cs2AgBiBr6 absorber (thermal-coupled device; added 2026-07-19)

| Parameter | Value used | Status | Source |
|---|---|---|---|
| Band gap Eg | 2.32 eV | [THEO, HSE06 indirect] | Eddekkar et al., *Micro and Nanostructures* 190 (2024) 207840 — chosen for SELF-CONSISTENCY with the same-paper HSE06 optics (onset sits at the HSE06 gap). Report alongside: GW indirect 1.83 (L-X)/1.97 (Γ-X), GW direct 2.51 [Filip et al., JPCL 2016]; experimental Tauc 2.213 eV [Eddekkar Fig. 7]; PL 1.89 eV. The ~0.1–0.3 eV onset overestimate vs experiment = stated limitation |
| Electron affinity χ | 4.0 eV base, **[SWEPT] 3.79/4.0/4.19** | [SIM-LIT; both primaries confirmed to NOT report χ] | 3.79: PMC12464330 Table 1; 4.19: arXiv:2011.10851. Neither Eddekkar nor Filip reports χ/IP (confirmed by direct PDF read) |
| Rel. permittivity ε_r | 5.8 | [THEO, RPA ε∞ electronic-only] | Filip et al., JPCL 2016 (same value adopted by PMC12464330). Penn-model ε₁(0)=3.54 [Eddekkar] disclosed as alternative; NO experimental static (ionic-inclusive) ε_r exists — DISCLOSE. Low sensitivity expected (absorber near-intrinsic, fully depleted) |
| Effective masses | me*=0.33 (L-Γ; 0.20 X-Γ), mh*=0.84 (X-W) m0 | [THEO, HSE06; direction-dependent — DISCLOSE choice] | Eddekkar 2024 Table 1 |
| Nc, Nv (300 K) | 4.76e18 / 1.93e19 cm⁻³ | [DERIVED] 2(2πm*kT/h²)^1.5 from 0.33/0.84 | standard formula; directional caveat above |
| Mobilities μn=μp | 0.57 cm²/Vs base (film mid of 0.39–0.74), **[SWEPT] vs 6 (crystal mid of 0.8–11.8)** | [EXP; ambipolar-unsplit — DISCLOSE] | parameter_sheet compilation (single-crystal + thin-film studies) |
| Doping | p-type, Na = 1.42e12 cm⁻³ | [EXP, as-grown, Ag-vacancy acceptors] **CITATION-CHECK FLAG — primary not re-confirmed** | parameter_sheet; must chase the primary before submission |
| τ_SRH | 13.7 ns base, **[SWEPT] vs 1 µs** | [EXP, film TRPL biexp 2.5/35 ns → τ_eff; effective NOT pure-SRH — DISCLOSE] | parameter_sheet (film study; ">1 µs" annealed-film study = sweep upper) |
| Radiative B | 3.19e-12 cm³/s | [DERIVED, van Roosbroeck–Shockley, stage47] | from σ-route α(E), n(E) + derived Nc,Nv + Eg 2.32. Onset-tail sensitive (1.4e-10 from 2.2 eV / 1.3e-14 from 2.5 eV) — DISCLOSE; radiative ≪ SRH at ALL these values, so immaterial to results (contrast FASnI3) |
| n(λ), k(λ) | `Cs2AgBiBr6_nk_Eddekkar2024.csv` | [THEO HSE06, digitized; n text-anchored] | n: Eddekkar Fig. 6f (n(0)=1.88 anchor, ±0.005). k: **σ-route** — Fig. 6b σ(ω) pixel-traced → ε₂=4πσ/ω → k=ε₂/2n, cross-validated vs Fig. 6c ε₂ peak (3.86 vs ~3.9 @ 4.6 eV). **PROVENANCE FINDING: Fig. 6a's α axis is internally inconsistent by ~2π** (pointwise ratio σ-route/panel-a = 6.33±0.05 vs 2π=6.28 over 3.2–5.5 eV; panels b,c,f mutually consistent) — panel (a) NOT used; phrase politely in SI. Effective onset (α>10³/cm) 2.34 eV = 530 nm |
| Thermal κ (absorber) | 0.36 W/mK | [EXP, FDTR] | "Dynamic Local Order and Ultralow Thermal Conductivity of Cs2AgBiBr6", *Nano Lett.* 2024 |

### Thermal model auxiliary κ values (Cs2AgBiBr6 device only)
| Layer | κ [W/mK] | Status | Source |
|---|---|---|---|
| TiO2 (thin film) | 1.2 (meas. 0.7–1.7 for 150–300 nm) | [EXP, thermo-reflectance] | Mun, Kim, Kato, Hatta, Lee, Kang, *Thermochim. Acta* 455 (2007) 55–59 |
| Spiro-OMeTAD | 0.2 | [ESTIMATE — no direct measurement exists; bracket PCBM 0.05–0.06 ↔ DNTT 0.45±0.06] | Wang et al., *Sci. Rep.* 5:16095 (2015) + refs therein; DISCLOSE as organic-typical estimate |
| FTO (SnO2:F) | 4.5 (meas. 4.4–4.9, 200 nm polycryst. SnO2-TCO; dopant species shown immaterial) | [EXP, pulsed-light thermoreflectance] | Oka, Yamada, Yagi, Taketoshi, Jia, Shigesato, *J. Mater. Res.* 29 (2014) 1579–1584 |
| Au | 317 (bulk) | [EXP, standard reference] | CRC Handbook / Ho, Powell, Liley, *J. Phys. Chem. Ref. Data* 1 (1972) 279 |

### Thermal model disclosures (methods/SI)
- Steady state ⇒ Cp not required (genuinely absent from literature for this compound anyway).
- Q = total absorbed EM power (neglects extracted electrical power ≤ few % and radiative escape) ⇒ conservative upper bound on heating.
- Heat source from the 300–900 nm sweep; NIR > 900 nm (~30% of AM1.5G power, mostly Au-reflected) neglected.
- h_conv swept 5/10/20 W/m²K (combined natural convection+radiation range; no device-specific literature value exists); T_amb = 300 K; lateral faces insulated (periodic unit cell).
- Sequential (one-way) coupling ht → T_op → J-V; bidirectional feedback ≤ few % at these PCEs. Eg(T) NOT included — no literature dEg/dT for Cs2AgBiBr6.
- Internal conduction resistance ~1e-6 m²K/W ≪ 1/h ⇒ stack near-isothermal; T_op controlled by h, not by κ values.
- **Heat-source magnitude caveat**: the broadband Q is dominated by FTO/Au parasitic absorption, and the FTO optical constants are placeholder-grade (flat k=0.02, ~10× real FTO) — same as all devices in this study (architecture consistency). Report BOTH the full-Q T_op and the absorber-only-heating lower bound (analytic, isothermal limit); frame full-Q as an upper-bound-type estimate.
- Methodology precedents to cite: Saxena & Gorji, *IEEE J. Photovolt.* 9 (2019) 1693 (MAPbI3 optical-electrical-thermal 3D COMSOL); **Kamppinen, Palonen, Miettunen, *ACS Appl. Energy Mater.* 7 (2024) 4324, doi 10.1021/acsaem.4c00077 (perovskite self-heating opto-electro-thermal model, 1D TMM/net-radiation)** — our differentiators: 3D FEM full-wave optics, the Cs2AgBiBr6 compound, fully cited κ stack, honest h-sweep. Electrical-only prior art on THIS compound: arXiv:2602.15759 (no thermal) — cite and differentiate.

## 3c. Cu2AgBiI6 (CABI) absorber (added 2026-07-19; the family's best device)

| Parameter | Value used | Status | Source |
|---|---|---|---|
| Band gap Eg | 2.03 eV | [EXP, Elliott fit of the SAME ellipsometry dataset as our optics] | Kamppinen et al., *Adv. Opt. Mater.* 2026, 14(5), e03237 Table 1. Disclose method-dependence (excitonic): Tauc 1.98 (their sim choice), CP 2.09, Sansom Elliott 2.06(1), Pai film 1.89 |
| Electron affinity χ | 3.22 eV, **[SWEPT] 3.16/3.22/3.36** | [DERIVED from two EXP quantities] | PESA IP = 5.25±0.05 eV [Pai et al., *Adv. Energy Mater.* 2022, 12, 2201482] minus Elliott Eg 2.03; sweep endpoints = IP−CP gap and IP−Pai gap (all traceable) |
| Rel. permittivity ε_r | 6.3, **[SWEPT] 12** | [DERIVED ε∞=n(NIR)² from our own optics file; electronic-only — NO static value exists, DISCLOSE] | Kamppinen tabulated n; result: ~nil sensitivity |
| Effective masses | me*=0.6, mh*=1.0 m0 (in-plane) | [THEO, DFT] | Sansom et al., JACS 2021 |
| Nc, Nv (300 K) | 1.166e19 / 2.509e19 cm⁻³ | [DERIVED, T_dev-scaled closed form] | standard formula |
| Mobilities µn=µp | 1.7 cm²/Vs, **[SWEPT] 5.1** | [EXP, THz sum mobility 1.7(5); ambipolar-unsplit + localization caveats — DISCLOSE] | Sansom JACS 2021 / ACS Energy Lett. 2021 (delocalized 2.1–5.1) |
| Doping | p-type Na=1e12, **[SWEPT] 1e15** | **[ASSUMPTION — no literature doping data exists; weak-p typical of Cu-halides]** | dedicated search 2026-07-19; result: immaterial (±1.5% rel) |
| τ_SRH | 33 ns, **[SWEPT] 3.3** | [EXP, TRPL stretched-exp avg; STE/polaron-influenced effective lifetime, NOT pure SRH — DISCLOSE] | Sansom JACS 2021; strongest sensitivity axis |
| Radiative B | 1.51e-10 cm³/s | [DERIVED, VRS, stage54] | from the nk file + Nc,Nv,Eg above; onset sensitivity (from 2.1 eV: 1.3e-11) disclosed |
| n(λ), k(λ) | `Cu2AgBiI6_nk_Kamppinen2026.csv` | [EXP, TABULATED ellipsometry — NO digitization + PDS sub-gap splice] | n & k≥2.0 eV: Kamppinen Zenodo 10.5281/zenodo.17899531 (mean of samples; ~10% spread above gap; ~1.8× above the digitized Sansom PDS α — inter-experiment spread, DISCLOSE); k<2.0 eV: Sansom PDS decay shape anchored at the ellipsometry k(2.0) (the raw ellipsometry sub-gap floor is a roughness/EMA artifact ~20× PDS); k=0 below 1.40 eV. Anchors verified: n(300)=1.95/n(435)=2.63/n(610)=2.99/k(565)=0.771→α=1.72e5 |
| Thermal | NOT modeled — no κ exists for CABI (searched); thermal coupling is the Cs2AgBiBr6-only feature, state explicitly | [GAP] | |

## 4. Transport layers and contacts (shared)

### TiO2 (ETL, both devices)
| Parameter | Value | Status | Source |
|---|---|---|---|
| Eg | 3.2 eV | [SIM-LIT, 2 sources agree] | Rahman et al., *RSC Adv.* 2023 (10.1039/d3ra02170j) Table 2; Usman & Bovornratanaraks, *ACS Omega* 2024 Table 1 |
| χ | 4.15 eV (mid of 4.1/4.2) | [SIM-LIT] | same two sources |
| ε_r | 9.5 | [SIM-LIT] | same |
| Nc / Nv | 2.2e18 / 1e19 cm⁻³ | [SIM-LIT; Nv disagrees across sources — 1e19 (Rahman) vs 2.2e18 (Usman); Rahman used — DISCLOSE] | same |
| μn / μp | 20 / 10 cm²/Vs | [SIM-LIT, both agree] | same |
| Doping | n-type, Nd = 5e17 cm⁻³ (mid of 1e17–1e18) | [SIM-LIT] | same |
| n(λ) | Devore Sellmeier n=√(5.913+0.2441/(λ²−0.0803)), λ in µm; k=0 | [EXP] | Devore, *J. Opt. Soc. Am.* 41, 416 (1951). k=0 even below 387 nm → slight UV generation overestimate — DISCLOSE |

### Spiro-OMeTAD (HTL: BaZrS3 comparison case; FASnI3 primary)
| Parameter | Value | Status | Source |
|---|---|---|---|
| Eg | 2.9 eV | [SIM-LIT; 3.2 in Tiwari — disagreement, Rahman used] | Rahman 2023 / Tiwari et al., *Nanomaterials* 2022, 12, 2506 |
| χ | 2.15 eV (mid of 2.1/2.2) | [SIM-LIT, agree] | both |
| ε_r | 3 | [SIM-LIT, agree] | both |
| Nc / Nv | 2.2e18 / 2.2e18 cm⁻³ | [SIM-LIT; Tiwari's Nv=1.8e19 flagged; Rahman used] | Rahman 2023 |
| μn = μp | 1e-4 cm²/Vs | [SIM-LIT; Tiwari's "2e4" rejected as transcription error — DISCLOSE reasoning] | Rahman 2023 |
| Doping | p-type, Na = 1e18 cm⁻³ (LOW end of 1e18–1e20 lit range — chosen because Na must stay < Nv for MB statistics; documented) | [SIM-LIT] | Rahman 2023 |
| n, k | 1.75 / 0 flat | **[PLACEHOLDER]** | not literature-pinned — disclose (back-of-absorber layer, second-order for optics) |

### CuO (HTL: BaZrS3 final device)
| Parameter | Value | Status | Source |
|---|---|---|---|
| Eg | 1.2 eV | [SIM-LIT] | Sci. Rep. 2024 (PMC10982297) Table 1 (their refs [46],[58],[59]) |
| χ | 4.07 eV | [SIM-LIT] | same |
| ε_r | 18.1 | [SIM-LIT] | same |
| Nc / Nv | 3e19 / 5.5e20 cm⁻³ | [SIM-LIT] | same |
| μn / μp | 200 / 20 cm²/Vs | [SIM-LIT] | same |
| Doping | p-type, Na = 1e16 cm⁻³ | [SIM-LIT] | same |
| n(λ), k(λ) | `CuO_nk_Ungeheuer2023.csv` | [EXP, ellipsometry, digitized] | Ungeheuer, Marszalek, Mitura-Nowak, Rydosz et al., *Sci. Rep.* 13 (2023), Fig. 4e non-implanted "main layer"; validated vs their Fig. 4a: α(4 eV) 3.81e5 vs ≈3.9e5 cm⁻¹ (2%) |
| Photogeneration in CuO | NOT counted (parasitic absorption only) | modeling choice | conservative vs the source paper, which treats CuO as a second absorber (their 27.03% not 1:1 comparable) — DISCLOSE |

### Other layers
| Layer | Optics | Status | Source |
|---|---|---|---|
| Au back contact | tabulated n,k, 141 points | [EXP] | McPeak et al., *ACS Photonics* 2, 326 (2015) (`Au_McPeak2015_nk.csv`) |
| FTO | n=1.9, k=0.02 flat | **[PLACEHOLDER]** | not literature-pinned — disclose; FTO is optics-only + ideal contact |
| Air | n=1 | — | — |

---

## 5. Results actually quotable (for the manuscript)

### BaZrS3 (forward bias; ideal Jsc ceilings: 12.29 mA/cm² Spiro-optics / 11.44 CuO-optics)
| Stack | Case | Jsc | Voc | FF | PCE |
|---|---|---|---|---|---|
| CuO HTL | χ4.1, τ1ns (base) | 9.19 | 0.390 | 0.690 | 2.47% |
| CuO | τ33ns | 11.34 | 0.401 | 0.751 | 3.41% |
| CuO | χ4.0 / χ3.9 | 9.72 / 10.65 | 0.389 / 0.506 | 0.657 / 0.542 | 2.49 / 2.92% |
| Spiro HTL | χ4.1, τ1ns | 11.85 | 1.341 | 0.340 | 5.40% |

Mechanisms: Spiro → Voc at radiative bound (1.41 V computed) but 0.93 eV valence cliff → S-shape, FF 0.34. CuO → healthy FF but ΔEc≈0.03 eV (no e-blocking) → leakage-limited Voc (dark ideality ≈1.1, J0≈1e-5 mA/cm²); χ=3.9 (ΔEc 0.17) lifts Voc to 0.51 V. QF vs thermionic interface limits agree to 0.2%. EQE: peak 0.539@500 nm; EQE-integrated Jsc 9.14 vs 9.19 (0.5%). Design rule: BaZrS3 needs an HTL with deep HOMO (~5.9 eV) AND high CBM — neither Spiro nor CuO provides both.

### FASnI3 (Spiro HTL; ideal Jsc 18.27 mA/cm²)
| Case | Jsc | Voc | FF | PCE |
|---|---|---|---|---|
| base (χ3.50 exp, τ43ns, ε8.2, μ67) | 14.74 | 0.987 | 0.517 | 7.52% |
| χ3.75 / χ4.0 | 15.15 / 15.42 | 0.985 / 0.984 | 0.693 / 0.768 | 10.34 / 11.64% |
| τ123ns | 14.74 | 0.987 | 0.517 | 7.52% (identical) |
| ε6 / ε10 | 14.49 / 14.90 | ~0.986 | ~0.52 | ~7.5% |
| μ22 | 13.26 | 0.996 | 0.453 | 5.98% |

Mechanisms: Voc pinned at VRS radiative ceiling (0.98 V) in all cases (bulk SRH proven irrelevant); FF controlled by TiO2/FASnI3 ΔEc (0.65 eV @χ=3.50 → 0.15 @χ=4.0). Dark turn-on 0.9–1.1 V.

### Cs2AgBiBr6 (Spiro HTL; ideal Jsc 2.07 mA/cm²; THE THERMAL-COUPLED DEVICE; added 2026-07-19)
| Case | Jsc | Voc | FF | PCE |
|---|---|---|---|---|
| base (χ4.0, τ13.7ns, ε5.8, µ0.57, 300 K) | 2.010 | 1.711 | 0.286 | 0.98% |
| χ4.19 | 1.989 | 1.571 | 0.241 | 0.75% |
| χ3.79 | 2.016 (Jsc only) | — | — | EXCLUDED: multivalued S-NDR solver branches (dark+light, both hetero modes; dark branch carries thermodynamically impossible reverse current) — quote as a numerical-limits disclosure, not a device result |
| τ=1 µs | 2.066 | 1.853 | 0.453 | 1.73% |
| µ=6 | 2.061 | 1.727 | 0.413 | 1.47% |
| ε3.54 | 2.010 | 1.626 | 0.302 | 0.99% (negligible) |
| T_op 308.9 K (h=20) | 2.009 | 1.709 | 0.283 | 0.970% |
| T_op 317.7 K (h=10) | 2.007 | 1.707 | 0.280 | 0.959% |
| T_op 335.5 K (h=5) | 2.004 | 1.675 | 0.281 | 0.942% |

Thermal: T_op = 335.5/317.7/308.9 K at h=5/10/20 W/m²K (full-Q, 353.6 W/m²; absorber-only bounds 306.2/303.1/301.6 K); stack isothermal to 0.19 mK. **Temperature coefficient ≈ −0.12%/K RELATIVE** (vs Si −0.4%/K) — blocked-injection Voc is T-insensitive; Eg(T)/µ(T)/τ(T) excluded (no literature data, disclosed). Mechanisms: collection near-ideal (97–100% of optics ceiling); FF collapsed by the 1.27 eV absorber→Spiro VBM cliff (family-worst BaZrS3 pattern); dark J≈0 to 1.9 V (hole injection blocked); SRH-limited NOT radiative-pinned (contrast FASnI3).

### Cu2AgBiI6 (Spiro HTL; ideal Jsc 13.91 mA/cm²; BEST DEVICE OF THE FAMILY; added 2026-07-19)
| Case | Jsc | Voc | FF | PCE |
|---|---|---|---|---|
| base (χ3.22, τ33ns, ε6.3, µ1.7, Na1e12) | 13.856 | 1.512 | 0.473 | **9.91%** |
| χ3.16 / χ3.36 | 13.855 / 13.856 | 1.517 / 1.502 | 0.445 / 0.504 | 9.36 / **10.49%** |
| τ=3.3 ns | 13.453 | 1.499 | 0.365 | 7.36% (strongest axis) |
| µ=5.1 | 13.886 | 1.499 | 0.517 | **10.75%** |
| ε12 / Na1e15 | 13.85 / 13.86 | 1.52 | 0.47 / 0.48 | 10.0 / 10.0% (both ~nil) |

Mechanisms: collection 99.6% of the optics ceiling; **ETL-cliff-limited (0.79–0.99 eV electron cliff at TiO2) — INVERTED vs the HTL-cliff pattern of BaZrS3/Cs2AgBiBr6**; Spiro hole cliff only 0.14–0.34 eV; dark turn-on ~1.5 V; SRH-limited (τ axis dominates); assumed doping immaterial. Cross-checks vs Kamppinen 2026: ideal Jsc 13.91 vs their J_ph 12.9 (220 nm, real FTO — consistent); our 9.9–10.7% sits sensibly under their 20% solar radiative limit. NUMERICAL disclosure: 25 mV sweeps hit spurious S-NDR branches at low V under illumination (ETL-cliff-correlated); dense 5 mV continuation eliminated them (0/221 points; metrics of record from dense curves for base and χ3.36); a mild ≤+10% elevated-J residual below 0.55 V remains in the χ3.36 curve (Jsc/MPP/Voc unaffected).

---

## 6. Mandatory methods/SI disclosures checklist

1. Digitization methodology (pixel tracing, calibration, achromatic masks) + per-spectrum validation anchors (all listed above) — and that digitized spectra should be spot-checked with WebPlotDigitizer before submission (project standard).
2. KK construction for BaZrS3 (Δε₁=+3.95 truncation offset, anchor n=2.75).
3. VRS-derived B values and the relation used.
4. χ(BaZrS3) provenance chain (primary DFT SI inaccessible → simulation-literature value + sweep).
5. Ambipolar mobility treatment for FASnI3 (single FET value used for both carriers).
6. τ values are effective PL lifetimes (trap-influenced), not pure SRH capture parameters — per-material caveats in parameter_sheet.md.
7. Ideal ohmic contacts; no interface traps in baseline; the two heterointerface transport limits and their agreement.
8. FTO and Spiro optical constants are placeholders (flagged); TiO2 UV transparency (Devore k=0).
9. CuO parasitic-only photogeneration (vs source paper's second-absorber treatment).
10. AM1.5G = ASTM G173-03 global tilt, P_in = 1000.37 W/m²; earlier direct-spectrum error caught and corrected (do not cite old Gz profiles).
11. Cracked-license situation must be resolved before submission (see SESSION_HANDOFF §4).

## 7. File map (data → figure/result)

| File | Content |
|---|---|
| `BaZrS3_nk_KK.csv`, `CuO_nk_Ungeheuer2023.csv`, `FASnI3_nk_Ghimire2017.csv`, `Au_McPeak2015_nk.csv` | optical constants used by ewfd |
| `AM15G_ASTM_G173_global.csv` | spectrum |
| `BaZrS3_Gz_profile_AM15G_CuO.csv`, `FASnI3_Gz_profile_AM15G.csv` | generation profiles (production) |
| `results/jv_fwd_cuo*`, `results/jv_fwd_spiro*`, `results/jv_fasni3_*` | J-V curves (forward) |
| `results/metrics_summary_cuo_fwd.json`, `results/metrics_summary_fasni3.json` | metrics of record |
| `results/BaZrS3_EQE_CuO.csv` | EQE |
| `results/band_diagram_eq_ramp1.csv` | BaZrS3 equilibrium band diagram (Spiro-era, χ=4.1) |
| `results/figures/*.png` | draft figures |
| `papers/` | local PDFs of directly-read sources (incl. `fasni3_optics.pdf`) |
| `Cs2AgBiBr6_nk_Eddekkar2024.csv` | Cs2AgBiBr6 n,k (σ-route; stage47; 2π provenance finding documented in header) |
| `Cs2AgBiBr6_Gz_profile_AM15G.csv`, `Cs2AgBiBr6_optical_absorption_AM15G.csv` | Cs2AgBiBr6 generation + per-layer absorption (stage49, 300–900 nm) |
| `Cs2AgBiBr6_Qtot_profile.csv` / `_norm.csv` | broadband heat-source profile (raw binned / per-layer power-conserving renormalized — ht uses `_norm`) |
| `results/Cs2AgBiBr6_thermal_Top_vs_h.csv`, `_Tz_profiles.csv` | thermal solve outputs (stage50) |
| `results/jv_cs_*.csv`, `results/Cs2AgBiBr6_metrics.csv` | Cs2AgBiBr6 J-V curves + metrics of record (stage51/52; chi3p79 files retained as the multivalued-branch evidence) |
| `Cu2AgBiI6_nk_Kamppinen2026.csv` | CABI n,k (tabulated ellipsometry + PDS sub-gap splice; stage53; provenance in header) |
| `Cu2AgBiI6_Gz_profile_AM15G.csv`, `Cu2AgBiI6_optical_absorption_AM15G.csv` | CABI generation + per-layer absorption (stage55, 300–900 nm) |
| `results/jv_cabi_*.csv`, `results/Cu2AgBiI6_metrics.csv` | CABI J-V + metrics of record (stage56/56b/57; `_dense` = 5 mV curves used for base & χ3.36) |
| `papers/kamppinen2026_ellipsometry.pdf` (symlink) | Kamppinen 2026 local PDF; Zenodo data in job tmp + values baked into the nk CSV |
