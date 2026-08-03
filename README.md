# Full-wave 3-D opto-electro-thermal simulation of four lead-free perovskite absorbers

Simulation inputs, results, analysis scripts and figure code for:

> **Interface Band Offsets, Not Optical Collection, Limit Four Chemically
> Distinct Lead-Free Absorbers: A Full-Wave 3-D Opto-Electro-Thermal Study**
> Md. Mohiuddin and Alamgir Kabir, Department of Physics, University of Dhaka.

Four lead-free absorbers — BaZrS₃, FASnI₃, Cs₂AgBiBr₆ and Cu₂AgBiI₆ — are
placed in one fixed device architecture and compared on identical optical,
electrical and numerical footing. Maxwell's equations are solved on the real
multilayer stack rather than a generation profile being assumed, and the
resulting G(z) drives a drift–diffusion transport model.

**Start with [`REPRODUCE.md`](REPRODUCE.md).** It documents the pipeline end to
end and, in Section 6, four traps that silently produce plausible but wrong
answers.

## Headline results

Optical current ceilings (AM1.5G, 100 % collection, mA cm⁻²):

| Absorber | Prescribed-profile estimate | Full-wave 3-D | Change |
|---|---:|---:|---:|
| FASnI₃ | 18.27 | **20.450** | +11.9 % |
| Cu₂AgBiI₆ | 13.91 | **15.083** | +8.4 % |
| Cs₂AgBiBr₆ | 2.07 | **2.546** | +23.0 % |
| BaZrS₃ | 12.29 | **10.306** | −16.1 % |

Device metrics on the corrected optics:

| Absorber | J_sc (mA cm⁻²) | V_oc (V) | FF | PCE |
|---|---:|---:|---:|---:|
| FASnI₃ | 15.811 | 0.988 | 0.509 | 7.95 % |
| Cu₂AgBiI₆ | 15.017 | 1.384 | 0.518 | 10.76 % |
| BaZrS₃ | 9.883 | 1.337 | 0.340 | 4.48 % |
| Cs₂AgBiBr₆ | 2.473 | 1.766 | 0.280 | 1.22 % |

No device is limited by optical collection (96–99.6 % of ceiling collected);
each is limited by a band-offset cliff at a transport interface.

## Layout

```
data/optical_constants/   n,k for every material (lambda_um, n, k)
data/reference_spectra/   AM1.5G, ASTM G173 global tilt
results/optical/          per-wavelength absorptance and loss budget
results/generation/       G(z), optical frame and transport frame
results/jv/               every J-V curve, including control runs
results/mesh/             mesh statistics and convergence data
scripts/full3d/           optical pipeline (stages 01-14)
scripts/transport/        device J-V runners and metric extraction
scripts/figures/          figure generation for the paper
manuscript/               manuscript, supplementary, figures, parameter tables
```

## Validation

Every result carries two independent checks: the optical energy budget must
close, and the depth integral of G(z) must reproduce the photocurrent obtained
separately from the spectral integral of layer absorptance.

| Check | FASnI₃ | Cu₂AgBiI₆ | BaZrS₃ | Cs₂AgBiBr₆ |
|---|---:|---:|---:|---:|
| Budget closure | −0.00 % | +0.00 % | +0.00 % | +0.00 % |
| Worst energy residual | −1.36 % | −1.39 % | −1.43 % | −1.35 % |
| G(z) vs spectrum | +0.05 % | +0.03 % | +0.04 % | −0.04 % |
| Band seam, 400 / 600 nm | 0.070 / 0.023 % | 0.079 / 0.020 % | 0.075 / 0.020 % | 0.096 / 0.000 % |

Each device re-simulation was additionally preceded by a control run on the
previous generation profile that had to reproduce the published base case
before the new result was accepted. All four controls reproduced exactly.

## Not included

COMSOL `.mph` model files (63–115 MB each) are omitted: they exceed GitHub's
file-size limit and are fragile across COMSOL versions. They rebuild from the
scripts, which is the supported path. Contact the corresponding author if the
binaries are required.

## Requirements

COMSOL Multiphysics 6.2+ with Wave Optics and Semiconductor modules; Python 3.8+
with MPh, JPype1, NumPy and Matplotlib. See `REPRODUCE.md` for detail.

## Citing

Please cite the paper above. If you use the corrected optical constants, cite
their original sources as listed in `manuscript/MANUSCRIPT_PARAMETER_TABLES.md`.

## License

Code is released under the MIT License. Optical constants and the reference
spectrum are redistributed from their original sources under the terms of those
sources; see the header line of each file for provenance.
