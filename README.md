# PP — VLEO research package / PP-1.0

This package is a **new algorithm version**, written from scratch to make the behavior of the Python and MATLAB implementations explicit. It neither calls nor modifies legacy project files, and it does not present legacy experiments as its own results. Verification of a numerical model and validation of a real spacecraft are separate tasks. The checks performed here do not complete the latter. In particular, cross-language agreement cannot be claimed without running MATLAB.

**English documentation edition:** this is a translation of the patch 2 delivery documentation. Equations, parameter values, source code and fixtures are unchanged. Historical verification statements below describe the package preparation stage; they have not been rewritten to incorporate later user runs or the completed pilot analysis. No new simulation was performed for this translation. The file manifest has been refreshed to cover the translated documents. If you run this English-documentation copy, its MATLAB gate requires a fresh `verify_pp('full')`; reading these documents alone does not require rerunning experiments. Keep the existing working project and its results intact.

## Numeric-type correction — PP-1.0 patch 2

Six quick tests passed in the user's local MATLAB run. In the first full-duration RQ1/periodic comparison, all result metrics matched and command differences were approximately 1e-19 N /1e-14 W, yet the first 20 trace columns differed by up to approximately 0.5. Cause: SciPy stored `main_duration_days=30` and `common_settlement_days=7` in the MAT file as `int64`, whereas the short durations were `double`. MATLAB's mixed integer/floating-point arithmetic and concatenation rules propagated the integer type into the time counter and trace row. Rounding the first 20 trace columns to integers while preserving the command columns subsequently overwritten reproduced the reported 30-column error vector to within 1.16e-14. This explains the recording/type origin of the reported failure; it does not establish that all MATLAB cases pass.

`pp_numeric_spec` converts numeric parameters to `double` at the model input boundary. Count parameters retain integer values; only their storage type changes. MAT fixtures, expected traces, the Python core, parameter values and tolerances were unchanged. `pp_type_selftest` checks identical simulation/trace results for equal-valued double/int64 inputs and preservation of fractional trace values. `verify_pp` also reports the time, column, actual/expected value and tolerance of the first trace mismatch, if any. Full MATLAB verification must be rerun locally after this correction.

Type rules: [MathWorks — Combining Integer and Noninteger Data](https://www.mathworks.com/help/matlab/matlab_prog/combining-integer-and-noninteger-data.html). Extract the corrected package into a new directory and use the same startup commands; an old report cannot bypass the verification gate.

## Previous compatibility correction — PP-1.0 patch 1

The previous package invoked Java for SHA-256 and result-directory identifiers. Both direct Java dependencies were removed; the numerical model, fixtures and success/tolerance rules were unchanged. SHA-256 now uses PowerShell `Get-FileHash` on Windows, `sha256sum` on Linux and `shasum` on macOS. File paths are passed as data through an environment variable, not interpolated into shell commands. Verification first tests known SHA-256 digests for an empty file, `abc` and binary bytes 0–255. Paths containing spaces and square brackets are also tested. Hash verification remains enabled. If the native helper is unavailable, an explanatory error is raised rather than bypassing verification. Windows implementation reference: [Microsoft Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-5.1).

Extract corrections into a new directory; do not mix old and new sources. Updating the source manifest invalidates the old successful MATLAB report. Run the same three startup commands again. This change does not claim that the MATLAB UI works without a JVM on every platform; it removes direct Java calls from the package sources. MATLAB/Windows was unavailable in the development environment, so Windows command execution and MATLAB execution require local verification.

## 1. Research questions and mission contract

| Item | RQ1 | RQ2 |
|---|---|---|
| Research objective | Reliability–fuel tradeoff for maintaining the initial mean orbit | Reliability–fuel tradeoff with a +950 m terminal target after the same service mission |
| Initial condition | 300 km reference altitude, offset 0 m | Same |
| Main mission | 30 days, three control policies | Same |
| Common settlement phase | 7 days, same settlement algorithm | Same |
| Terminal target | **0 ±10 m** | **+950 ±10 m** |
| Service requirement | Sampled mean semi-major-axis offset within ±1000 m throughout all 37 days | Same |

+950 m is **not added to RQ1**. It is RQ2's explicitly different terminal mission. This number is a mission requirement inherited from the previous workflow, not derived from a physical law in this package. +950 km is never used. Targets are stored in `config/missions.json`. These research-question titles are operational definitions; the authors must align them with the paper's final wording.

With shared inputs, each policy's first 30 days of commands and states must match between RQ1 and RQ2; the Python tests check this. RQ2's orbit raising begins after the main mission. Because the service requirement continues during settlement, the +950 m target leaves only 50 m below the upper service boundary. This is an intentional, demanding mission contract.

## 2. Quick start

### MATLAB — verify first

Desktop MATLAB R2021a or newer is required. Extract the ZIP and set its root as MATLAB's Current Folder:

```matlab
addpath(fullfile(pwd,'matlab'));
verify_pp('full');
PP_BASLAT;
% Alternatively: launch_rq1; / launch_rq2;
```

If `verify_pp('full')` fails, the experiment UI will not open. The error and `validation/matlab_validation.json` are retained. Do not relax thresholds to force a pass; inspect the first divergent command/state. No MATLAB execution report is included in this delivery because MATLAB/Octave was unavailable in the development environment. Source syntax was inspected with a parser; that is not a MATLAB execution test. Allowed numerical differences are fixed in `config/tolerances.json`. Discrete modes, requests and success indicators must match exactly. Branch sensitivity can cause local MATLAB verification to fail; the package is then not approved for production experiments.

The UI defaults to the saved shared 37-day input, displayed as **“Ortak kayitli 37 gun”**. In that mode, duration, density, mass and power availability come from the MAT file; the other on-screen numbers are ignored. The second option, **“Ortak kayitli kisa kontrol”**, is the short check in which some missions are expected to fail. The third, **“MATLAB yerel RNG (kesif)”**, is exploration with MATLAB's native RNG, using the on-screen mass/density/availability and a development seed in 72001–72030. The same seed number does not reproduce Python's atmosphere. All three policies use the same realization. Cancellation records a partial result as `cancelled`, not as success. UI strings are unchanged; these Turkish menu labels are retained here so they match the actual controls.

Each run creates a separate directory under `results/RQ1/…` or `results/RQ2/…`, containing the source-manifest digest, complete settings, actual input arrays, MAT traces and a CSV summary. Charts are shown in the UI; image files are not exported automatically. MATLAB trace CSV files contain numeric data without headers; the column dictionary is given below.

### Python

Use Python 3.10+; a separate environment is recommended:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python python/validate_python.py
python python/verify_fixtures.py
python python/run_pp.py --mode smoke --rq both
python python/run_pp.py --mode nominal --rq both --seed 72001
```

Numba compiles on the first call; this startup delay is separate from steady-state computation time. Without Numba, the core falls back to ordinary Python and can be much slower. `smoke` uses a 3-hour main mission and 1.5-hour settlement phase; failure to reach RQ2's target is expected. A smoke check is not intended to make every policy succeed. First check execution without errors and correct recording of failures.

The complete development pilot is **not started automatically**:

```bash
python python/run_pp.py --mode pilot --rq both
```

The new pilot contains 3 masses (25,35.6,50 kg) ×5 densities (5e-12,1e-11,2e-11,4e-11,8e-11 kg/m³) ×3 availability fractions (.6,.8,1) ×30 development seeds ×3 policies ×2 RQs = **8100 runs**, or 4050 per RQ. This differs from the old 2430-run design. The supplied seed argument is ignored in pilot mode; the pilot uses the fixed range 72001:72030. Full traces and shared inputs for each cell are saved, increasing storage and runtime costs; the complete campaign may require tens of GB or more depending on compression. The CSV is flushed after every run. There is no automatic resume or duplicate skipping: restarting after interruption creates a new directory. An unhandled exception remains visible in the terminal, and partial files are retained. These are development experiments, not independent final-validation tests.

## 3. Authoritative files

- `config/spec.json`: default numeric parameters and their units. Both languages read this contract.
- `config/missions.json`: RQ targets.
- `python/pp_core.py`, `matlab/pp_*.m`: the same model and decision rules implemented in two languages.
- `fixtures/shared_*.mat`: **identical saved inputs** and expected outputs generated in Python. MATLAB does not recreate them with its RNG.
- `fixtures/components.mat`: 640 actuator boundary examples and 9 estimator examples.
- `python/validate_python.py`: independent analytical/alternative-solver checks; expected values are not fitted to the implementation output.
- `python/build_fixtures.py`, `build_components.py`: developer tools, never invoked by the verifier. Source changes require fixture generation and review for a new package version. Regenerating expected outputs to conceal an error is not acceptable.
- `matlab/verify_pp.m`: fixed package/input/output comparisons covering sampled 30-column state/covariance traces, **every** command node and all result metrics.
- `MANIFEST_SHA256.json`: SHA-256 digests of delivered files, excluding itself and subsequently generated results. The MATLAB gate checks source files as well. This detects accidental changes; it is not a signed security or certification system.
- `docs/MATEMATIK.md`: equations and derivations.
- `docs/DENEY_PROTOKOLU.md`: comparison protocol and limits of the evidence.
- `docs/KARARLAR.md`: differences from previous versions and their rationale.
- `docs/DOGRULAMA_OZETI.md`: passed, pending and unperformed checks.

The original document filenames are retained to preserve links and project structure; their contents are English.

## 4. Parameters: meanings and rationale

| Field (unit) | Default | Rationale/status |
|---|---:|---|
| μ (m³/s²), R (m), g0 (m/s²) | 3.986004418e14; 6378137; 9.80665 | Earth and standard thrust-conversion constants used by this model |
| a0 (m) | R+300000 | VLEO research reference; mean a rather than instantaneous position altitude |
| m0 (kg), Isp (s), Tmax (N) | 35.6;550;0.00055 | Preserves the previous nominal design; not calibrated against measurements here |
| Cd, A (m²), H (m) | 2.2;0.04;50000 | Fixed ballistic coefficient/local exponential-atmosphere assumption |
| dt (s) | 30 | Discrete-control and RK4 grid; no universal convergence guarantee |
| Power period / availability | 5400 s;0.6 | Synthetic schedule, not a solar-array/battery calculation |
| Allocated / nominal power | 80 W /50 W | Power available to propulsion only, not total platform power |
| Warmup / minimum ON | 600 /900 s | Design constraints, not verified against a manufacturer's thermal model |
| Cooldown / minimum OFF | 1200 /1800 s | **Sequential**, giving at least 3000 s of rest in total |
| Minimum throttle | 0.1 Tmax | 55–550 µN while ON; zero while OFF |
| σb, σu, τu | .3;.15;2000 s | Engineering assumptions for log-atmosphere variability |
| σwhite, σcolored, τcolored | 5 m;5 m;300 s | Synthetic measurement model, not real sensor data |
| Prior a variance | 75 m² | Assumed initial uncertainty; **not measurement variance** |
| Hysteresis thresholds | -500,+300 m | Previous nominal policy, not an optimized setting |
| Predictive horizon | 900 s | Fixed short-term drag prediction |
| Settlement response time | 1200 s | Common settlement-controller gain |
| Settlement deadband | 1 m | Request switching threshold, distinct from the 10 m terminal tolerance |
| Final planning horizon | 5400 s | Last power period; finite candidate search |
| Thrust search / numerical tie | 14 iterations /0.05 m | Finite bisection and candidate preference rule |
| Model altitude domain | 200–400 km | Exiting sets completed=0; the bounds do not validate atmospheric accuracy |
| Periodic interval / gain | 43200 s /1 | Fixed 12-hour nominal reference, not a strongly optimized competitor |

Density is **not pressure**; its unit is kg/m³. 8×10⁻¹¹ is included in the pilot, but feasibility at that density is not assumed. Increased availability can alter closed-loop timing; lower success with a particular setting does not demonstrate that additional power is physically harmful.

## 5. What does randomness change?

The seed initializes a pseudorandom-number generator; it does not determine whether physical parameter values are correct. Python uses four named PCG64 streams: constant atmospheric bias b, OU atmosphere u(t), white measurement noise and colored measurement noise. They are separated by `SeedSequence([seed, stream_id])`. Extending the duration preserves the earlier atmosphere/measurement prefix. A fixed seed, version and configuration reproduce the same inputs; select another development seed to obtain a different realization.

The atmospheric multiplier exp(b+u) is positive and lognormal. b and u are not density themselves. Their distributions and correlations determine the synthetic atmosphere's statistical properties. To inspect the realization associated with a seed, examine its saved arrays and summaries. `MATH.md` explains the process and why the multiplier does not have mean 1. MATLAB twister/randn and Python PCG64 need not generate identical arrays from the same seed number; compare saved inputs, not seed labels.

## 6. Execution order and outputs

At each node, synthetic measurement error is added to the true orbit and the estimator is updated first. The controller then computes the request, actuator transition and applied thrust. RK4 advances the true a/m over one interval. Fuel, energy and service violations are accumulated. The estimator is predicted using **the thrust actually applied in that interval** and the interval's initial mass. The final-node measurement is diagnostic and produces no command. The controller cannot access true b/u. The planner does not read future atmospheric truth; it uses a conditional decay prediction.

Success is `qualified = service_pass AND terminal_pass AND resource_pass`:

- `completed`: the duration was completed, states are finite, mass is positive and the model remains within its domain.
- `service_pass`: completed, with |a-a0|≤1000 m at sampled nodes. This is not a continuous-time certificate between nodes.
- `terminal_pass`: completed, with true final |a-a_target|≤10 m. Reaching the target in the estimate alone is insufficient.
- `resource_pass`: no power excess or minimum-ON interruption, and mass–fuel accounting discrepancy <1e-8 kg.

completed=1 with qualified=0 is possible. Low fuel consumption in a failed mission is not a saving. `resource_pass` alone does not imply mission completion. The initial offset is 0 m and is inside the service band, so violation accounting starts at the first advanced node. Violation duration is the sum of right-endpoint-sampled steps, not an exact event duration.

Trace CSV/MAT/NPZ columns, using **one-based indexing**:

```
1 time_s; 2 a_offset_m; 3 mass_kg; 4 estimate_a_offset_m;
5 estimate_b; 6 estimate_u; 7 estimate_colored_m; 8 variance_a_m2;
9 variance_eta; 10 thrust_N; 11 power_W; 12 mode; 13 timer_s;
14 request; 15 fuel_g; 16 energy_Wh; 17 actual_log_drag;
18 measurement_m; 19 innovation_m; 20 innovation_variance_m2;
21 P11; 22 P12; 23 P13; 24 P14; 25 P22; 26 P23;
27 P24; 28 P33; 29 P34; 30 P44.
```

Estimated a is recorded as an offset from a0; the measurement column is absolute a in meters. Command columns describe the interval following the same node. Thrust/power/request are zero in the final row. The timer records time in the current mode before applying the interval. Fuel/energy are cumulative up to that node. The a component of P has the same variance in absolute and offset coordinates. `variance_eta=P22+2P23+P33`.

## 7. What was verified at delivery?

The authoritative machine-readable delivery record is `validation/python_validation.json`. Local repeats write `validation/local_python_validation.json` and `local_python_fixture_replay.json`, leaving the delivery evidence intact. Checks cover the analytical variable-mass thrust solution, independent DOP853 integration, a finite-difference Jacobian, Van Loan matrix-exponential covariance, Gaussian measurement conditioning, hand-calculated actuator boundaries, reproducibility, causality, RQ main-mission equivalence, accounting and invalid-input rejection. These are selected checks, not a proof over the full parameter space.

Fixtures are two development realizations: 73001 for the short check and 73002 for the nominal 37 days, each with 2 RQs×3 policies. Short-check failures are expected. Success in all six nominal runs for one development input does not establish a general success rate or fuel advantage. Numerical metrics are in `fixtures/fixture_ledger.json`. The 640 actuator and 9 estimator examples check cross-language implementation agreement, not independent physical truth.

At package preparation, MATLAB execution, interactive UI testing, an independent held-out campaign, NEES/NIS/coverage calibration, a new high-density capacity certificate and flight validation were not completed. Do not present them as completed on the strength of these delivery records. Python and MATLAB can agree while both are wrong, which is why analytical/alternative-solver checks are also included. Previously reserved test seeds were not opened or generated.

## 8. Development corrections

An early development check found missing estimator prediction in the simulation loop; this was corrected before the first successful test record. Numba rejected `float(bool)` conversions, so compilation was fixed using equivalent explicit 1/0 expressions. Finite-state and positive-innovation-variance checks were added. These corrections are recorded openly, and the final checks correspond to the final source revision. The verifier never rewrites expected fixtures. Source changes break the manifest and invalidate an existing successful MATLAB report.

This README and its supporting documents define the contract of **this PP implementation**. Rather than claiming complete correctness for a real atmosphere/thruster/sensor, they identify which assumptions have been checked, where, and which checks remain outside the delivered evidence.
