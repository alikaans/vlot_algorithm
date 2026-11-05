# Delivery verification summary

This is the translated verification record from package preparation, including the patch 2 feedback recorded at that time. It is not a newly executed test report or a retrospective update of later user experiments.

| Layer | Delivery status | Evidence/limit |
|---|---|---|
| Independent Python numerical checks | 22/22 passed | `validation/python_validation.json`; selected analytical/numerical examples |
| Python replay of saved inputs | 12/12 matched | 6 quick +6 nominal 37-day cases; zero state/command/metric differences |
| Python without JIT | 2/2 matched | Short RQ1/RQ2 hysteresis cases; different execution of the same algorithm |
| Actuator examples | 640 examples prepared | Expected values generated in Python; MATLAB verification pending |
| Estimator examples | 9 examples prepared | 3 densities ×3 step sizes; MATLAB verification pending |
| MATLAB syntax | No parser errors | Not a MATLAB execution or UI test |
| MATLAB numerical parity | **Not executed in the development environment** | Local `verify_pp('full')` required |
| MATLAB UI | **Not executed in the development environment** | Desktop MATLAB unavailable there |
| New development pilot | **Not executed during package preparation** | Optional command launches 8100 runs |
| Independent final test/coverage | **Not performed** | Freeze protocol and use separate data |
| Real-system validation | **Not performed** | Calibration/flight data required |

Selected numerical results: a error approximately 2.14e-8 m against the analytical variable-mass thrust solution; DOP853 differences of a few 1e-9 m for selected 15/30/60 s steps; local F difference 1.11e-16; Q difference 1.78e-15; Joseph covariance difference 7.11e-15. These small errors do not establish physical atmospheric accuracy or mission reliability.

Quick fixture 73001: RQ1 periodic has terminal error +79.7203 m and fails; the other two RQ1 policies have +3.0268 m and succeed. All three RQ2 policies fail to reach +950 m within the short duration. These failures are expected fixture outcomes. In full fixture 73002, all three policies have qualified=1 for both RQ1 and RQ2, with terminal errors approximately -2.1069 m/-2.0810 m. One development atmosphere cannot establish general success rates or policy superiority.

Old pilot success rates are not newly computed PP results. Density 8e-11 is included in the new design and component estimator examples; this does not establish that PP meets all mission conditions at that density.

SHA records tied to the final sources, Python/library versions and detailed check results are under validation/. Local repeat reports use the `local_` prefix. Verification does not modify delivered reference evidence or fixtures.

## User's local MATLAB feedback / patch 2

After the Java correction, the user reported that 6 quick cases passed and that parity stopped at the first full-duration RQ1/periodic case. All 16 result differences were zero; command differences were at floating-point rounding scale. Trace differences were explained and reproduced by integer-type propagation during row concatenation. This was partial execution evidence supplied by the user; MATLAB had not run in the development environment, and the full 12-case suite was not treated as passed. Patch 2 corrected the numeric-type input boundary. Local verify_pp('full') was required again for the same cases. The new pp_type_selftest was included for execution in MATLAB but was not executed in the development environment.
