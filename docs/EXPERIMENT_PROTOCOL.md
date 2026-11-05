# Experiment and paper protocol

## 1. Freeze the contract before examining outcomes

Mission definitions, success flags, parameter ranges, seed partitions, tuning budgets, analysis methods and tolerances must be frozen before outcomes are inspected. PP-1.0 is a **development version**. First pass the Python checks and full local MATLAB parity checks, then specify a separate test set. The package provides no command for opening or trying previously reserved test seeds. The old reserved ranges 40001:40030,50001:50300,60001:60300 were not generated during this development. A different numeric seed label alone does not prove statistical independence; record the seed plan and protection of unseen data.

Quick checks and nominal fixtures are not a final test set for policy selection. If 73001/73002 fixtures inform tuning, they are development data. The new pilot seeds 72001:72030 are also development data. A complete report must state which data selected settings and which data performed final evaluation.

## 2. Paired design

Within a (mass,ρ0,availability,seed) block, all three policies use the same b/u/white/colored measurement-error realizations. RQ1 and RQ2 also share that realization. Reusing streams across density/power/mass cells is a common-random-numbers design; the cells are not independent. Measurement-error arrays are shared, but actual observations differ when trajectories differ.

The pilot has 3×5×3=45 cells and 30 runs per policy/RQ in each cell. Within-cell success is reported over 30 Bernoulli trials; an overall rate is separately defined as an equal-weight mixture of cells. Those weights are not the actual distribution of operational environments. Report cell-level results as well as overall rates to retain mass/density/availability interactions.

## 3. Reliability

Keep all runs in success-rate denominators. Report completed, service, terminal, resource and qualified separately. Each cell may report s/n and a Wilson interval. For z=1.96,

    p=s/n, den=1+z²/n,
    center=(p+z²/(2n))/den,
    radius=z/den ×sqrt[p(1-p)/n+z²/(4n²)].

Because policies share realizations, do not compare their success rates as independent proportions. In a paired table with gains b and losses c, the difference is (b-c)/n. When b+c is small, prefer the exact binomial version of McNemar's test. If b+c=0, no difference was observed; equivalence has not been established. Report effect sizes and uncertainty. Across many cells/tests, prespecify the primary comparison or plan a multiple-testing correction.

Even n=30 with zero failures does not establish very high reliability: the 95% one-sided binomial lower success bound is .05^(1/30)≈0.905. Supporting 99% success with 95% one-sided confidence and zero failures requires at least ceil[ln(.05)/ln(.99)]=299 independent trials. This count does not validate the physical model or every heterogeneous cell.

## 4. Fuel/energy and selection

Plot consumption for all runs, mark failures separately and do not describe low failed-run consumption as savings. In blocks where A and B both qualify, compute Δm=mA-mB and relative difference 100(mA-mB)/mA. This result is **conditional on the common-success subset**, not an unconditional savings claim over the mission population. Always report the number of jointly successful blocks, each policy's total successes and excluded blocks. Without common successes, the comparison cannot be made.

A fuel–reliability plot should put fuel on x and success on y; do not silently remove failures to produce an average-fuel curve. Main-mission fuel is read at the trace node t=30 days; settlement fuel is total fuel minus that value. Apply the same split to energy. No separate main-mission qualified flag was defined; `main_max_violation` is available. Adding an intermediate success criterion requires a protocol revision.

If paired bootstrap is used for fuel, resample at the seed-block level, carrying the relevant policies and cells for a seed together. Within-cell results and the equal-weight cell aggregate are different estimands. A three-policy common-success set may differ from pairwise sets; figure captions must identify the chosen set. Do not hide success differences and claim Pareto superiority solely from conditional fuel.

## 5. Balanced tuning and capacity

The present periodic reference uses a fixed 12-hour interval and gain 1. Hysteresis outperforming it does not imply superiority over all periodic policies. For publication, allocate equal computation/search budgets to the three policies on development data. Prespecify search ranges for period/gain, thresholds, prediction horizon and common settlement settings. Do not retune on the final test set. If settings are tuned separately for each RQ, revisit claims of identical policies and matching main-mission behavior.

At high density, distinguish capacity limitations from timing/controller limitations. A simple necessary check compares d×m against time-averaged feasible thrust; warmup/cooldown/minON/minOFF reduce availability. Such an average inequality alone is not sufficient to guarantee terminal±10 m, sampled-band compliance and uncertainty tolerance. Capacity conclusions from the old model do not automatically transfer to PP's new controller. Feasibility requires a separate reachability analysis using the same actuator state machine; this was not completed in the package preparation.

## 6. Estimator consistency and numerical sensitivity

A separate development/validation campaign should examine true [a,b,u,c] minus x_hat, RMSE, bias, NEES=e^T P^-1 e and NIS=ν²/S. NIS is not automatically temporally independent; do not treat every time node as an independent sample. Report pointwise ±1.96√Paa coverage separately across runs and time, using block-level uncertainty. Correct RMSE does not establish correct coverage. Reasons to assess consistency include the fixed true initial a versus assumed prior, linearly interpolated truth versus continuous-OU filter approximation, nonlinear atmosphere and finite quadrature.

Assess closed-loop sensitivity to the nominal 30 s step separately. Comparisons at 15 s/30 s/60 s must use **the same physical inputs**; redrawing RNG inputs at each step size prevents attribution of differences solely to integration. Actuator durations and switching can change on the grid; report event-related command differences separately. Fixture agreement does not replace this convergence study.

## 7. Paper structure

1. Problem definition, two distinct terminal contracts and the meaning of a.
2. Physical/atmospheric/measurement and actuator models; sources and assumption status of parameters.
3. Three main-mission policies, common estimator and common settlement algorithm.
4. Independent numerical verification and shared-input Python–MATLAB parity.
5. Prespecified factorial experiment, tuning/test separation and statistics.
6. Cell-level RQ1/RQ2 reliability; main-mission/settlement fuel and energy; failure categories.
7. Conditional fuel comparisons only in valid common-success regions.
8. Coverage, step sensitivity, capacity and physical limitations.

The old 4500-run scan and 2430-run pilot are historical development findings. The old pilot's 246/810,673/810,674/810 successes and its unopened fuel-comparison gate must not be presented as PP results. The old two-state estimator, a separate four-state shadow-filter version and this package's common four-state estimator throughout the mission are different experiments.
