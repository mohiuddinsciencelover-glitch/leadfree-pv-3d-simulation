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

Results of record (AM1.5G; ceiling = photocurrent at 100 % collection):

| Absorber | Ceiling J_ph (mA cm⁻²) | J_sc | V_oc (V) | FF | PCE | Collection |
|---|---:|---:|---:|---:|---:|---:|
| FASnI₃ | 20.450 | 15.811 | 0.988 | 0.509 | 7.95 % | 77.3 % |
| Cu₂AgBiI₆ | 15.083 | 15.017 | 1.384 | 0.518 | 10.76 % | 99.6 % |
| BaZrS₃ | 10.306 | 9.883 | 1.340 | 0.340 | 4.50 % | 95.9 % |
| Cs₂AgBiBr₆ | 2.440 | 2.371 | 1.760 | 0.281 | 1.17 % | 97.2 % |

The Cs₂AgBiBr₆ ceiling is the thick-contact limit (see the Au-truncation
section of REPRODUCE.md).

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

The jv/ directory additionally contains regression fixtures
(`jv_f3dctrl_*.csv`, `jv_ctrl*.csv`): fixed-input runs used to confirm the
pipeline reproduces its reference outputs exactly before any configuration
change is trusted.

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
