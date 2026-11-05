# Design decisions, provenance and limitations

## Status of the sources

This reconstruction was designed from the mission requirements in the user conversation and a review of the shared Drive research archive. Legacy MATLAB/Python/RQ packages, pilot reports and the parallel researcher's four-state estimator work informed the design. They are reference material, not executable authorities assumed correct by default. The PP core imports no legacy modules. No files on Drive or in the parallel researcher's workspace were modified.

This document does not claim calibration against a particular manufacturer's hardware or a real atmosphere. Inherited numerical constants are explicitly labeled as **defaults** in the README table; their connection to external measurement evidence was not reverified here. Two-body/Gaussian relations are derived under the model assumptions. The publication bibliography must separately connect claims to genuine sources; no citations are fabricated here.

## Main changes from earlier projects

| Decision | PP implementation | Rationale/consequence |
|---|---|---|
| RQ1 target | 0 m | End at the initial reference orbit; no hidden +950 m target |
| RQ2 target | +950 m | Preserve the previous, distinct terminal mission separately |
| Estimator | [a,b,u,c] throughout the mission | Avoid mixing two-state and terminal shadow-filter handoff versions |
| Measurement R | 25 m² | Consistent with white sensor σ=5 m; Paa=75 is a different quantity |
| Process Q | Includes a/u cross terms | Preserve propagation of drag uncertainty into orbital uncertainty |
| Final settlement | 3 feasibility candidates +throttle bisection | Make the constrained final burn explicit and reviewable; no optimality claim |
| Randomness | Saved shared inputs and independent named Python streams | Avoid seed-label confusion across languages and duration-dependent stream shifts |
| Power | Explicit synthetic schedule | Identify that it does not replace a physical battery/thermal model |
| Success | Four separate indicators and joint qualified flag | Avoid treating duration completion alone as mission success |
| Experiment | New 45-cell, 5-density design | Includes 8e-11; do not pool it with the old 27-cell results |
| Software gate | Fixed fixtures +hashes +local MATLAB report | Avoid claiming MATLAB verification without execution |

These changes do not make old and new results directly comparable. An improvement claim requires rerunning the legacy version and PP on identical saved inputs, with separate version labels. Because the estimator and settlement controller changed together, attribution requires an ablation: old/new estimator ×old/new settlement with identical policy and inputs. This package does not silently reproduce the legacy algorithm.

## Verification and validation layers

1. Dimensional/algebraic verification: equation units and analytical solutions.
2. Independent numerical verification: DOP853, matrix exponentials, finite differences and hand-calculated actuator cases.
3. Shared-input implementation verification: Python/MATLAB states, commands, covariance and metrics.
4. Performance and estimator coverage on unseen experiments.
5. Calibration of the physical model against actual sensor/thruster/atmosphere data.

At package preparation, records existed for layers 1–2; layer 3 awaited local MATLAB execution; layers 4–5 were incomplete. Do not claim that every error has been eliminated or that the controller is the final scientific optimum. These are historical delivery statements, not an update incorporating subsequent user experiments.

## Known operational limitations

- The UI requires desktop MATLAB; an Octave GUI is not a target. Interactive UI execution was not tested in the development environment.
- MATLAB native-RNG mode is exploratory. Fixture verification does not certify every new setting scientifically.
- The UI calls the verified core. Calling numerical functions manually can bypass the entrypoint gate; it is not a security boundary.
- The Python runner checks the manifest. Do not assume the bundled verification report applies to every local software version; rerun validate_python.py locally.
- The core uses no persistent JIT cache. Platform/library differences can affect control branches.
- True b/u arrays are used only for truth propagation and diagnostic traces; policies cannot access future true atmosphere.
- Traces contain both truth and estimates; distinguish them in the paper's analysis.
- A successful nominal fixture alone does not establish the research hypothesis.
- The terminal planner scores minimum violation/error; it does not solve a fuel–energy multiobjective optimum.
- Low consumption in failures is not a saving; conditional fuel plots must be interpreted together with reliability.
- The model provides no continuous-time service guarantee. Large exponential-atmosphere deviations require calibration and numerical-domain checks.
- Applied thrust can change throttle continuously; no throttle slew-rate constraint is defined.
- Battery SOC, power-subsystem efficiency, actuator lifetime, start-count limits and thermal states are absent. Electrical-energy accounting does not establish solar-array/battery feasibility.
- Reverse thrust is unavailable. Lowering the orbit requires waiting for natural drag; overshoot of a high target can cause terminal failure.

## Reproduction

Keep the root manifest with the digest recorded in result metadata. Source changes require a new version/manifest and verification. Identical source text alone does not define an identical experiment: settings, mission, actual input arrays, time grid, actuator initial state and runtime version must also match. A shared fixture's seed is a traceability label; the authoritative cross-language evidence is the saved input vectors.

## PP-1.0 patch 1: SHA-256 without a JVM

The user reported a missing-JVM error inside `pp_sha256`. Because MATLAB had not run in the development environment, earlier checks had not detected this dependency. Native OS hashing replaced Java MessageDigest, and MATLAB tempname replaced Java UUID. Three fixed SHA-256 vectors were added to verify_pp. Equations, policies, input arrays, expected numerical results and tolerances were unchanged. The manifest and parser record were updated. Local MATLAB verification remained necessary.

## PP-1.0 patch 2: MAT integer types propagating into trace recording

SciPy stored the full fixture's day counts as int64. In MATLAB, the resulting integer time counter caused the concatenation expression containing the first 20 trace columns to round those values to integers. Command columns were subsequently overwritten in a separate assignment, and covariance upper-triangle entries were recorded in a separate double row, so those columns matched. In the user's full RQ1/periodic report, all 16 result-metric differences were zero. Reconstructing the same recording-rounding effect reproduced the entire reported trace-error vector to within 1.16e-14.

The correction converts numeric configuration fields to double at MATLAB model entrypoints. A type-invariance check and a first-trace-divergence diagnostic were added. Numerical equations, policy decision formulas, physical parameter values, original MAT fixtures and tolerances were preserved. At that correction's preparation stage, full local MATLAB parity had not yet been reported as passed; the package did not mark it as such.
