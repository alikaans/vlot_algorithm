# PP-1.0 mathematics and numerical operations

This document defines the code's mathematical contract. It uses standard two-body energy balance and Gaussian conditioning; legacy Python/MATLAB outputs are not treated as proof. The equations hold under the model assumptions: a near-circular orbit, tangential thrust/drag, orbit-averaged a, fixed Cd/A/Isp and a local exponential atmosphere. Eccentricity, inclination, J2, latitude/winds, eclipse geometry, battery dynamics and actual thermal dynamics are not resolved.

## 1. Orbit, drag, fuel and energy

Specific orbital energy per unit mass is ε=-μ/(2a). Circular speed is v=√(μ/a). For net tangential acceleration f=T/m-d, dε/dt=vf. Therefore μ/(2a²) da/dt=√(μ/a)f, giving

    da/dt = G(a) [T/m-d],     G(a)=2√(a³/μ).

Density and drag are

    ρ(a,t)=ρ0 exp[-(a-a0)/H + b + u(t)]
    d(a,m,b+u) = (1/2) ρ Cd A (μ/a)/m.

d is a positive acceleration magnitude and is subtracted in da/dt. ρ0 is the synthetic reference density at the initial reference orbit, not automatically the actual mean density. G has units of seconds, so G×acceleration has units of m/s.

With constant Isp, the rocket relation is dm/dt=-T/(Isp g0). Electrical power is P=50(T/Tmax) W while ON, 50 W during warmup, and zero during OFF/cooldown. This linear electrical relation is an engineering assumption, not a physical thruster-efficiency map. Warmup consumes energy but produces no thrust or propellant consumption. E_Wh=ΣP_k dt/3600 and m_fuel=ΣT_k dt/(Isp g0). Fuel is also reported from mass depletion; the discrepancy between these accounts is checked separately.

For RK4, T and the mass derivative are constant over each interval, while true η=b+u is interpolated linearly between nodes. k1=f(a,m,ηk); k2=f(a+h k1/2,m+h dm/2,(ηk+ηk+1)/2); k3 uses the same midpoint with k2; k4=f(a+h k3,m+h dm,ηk+1). Then a+=h(k1+2k2+2k3+k4)/6 and m+=h dm. This is not an exact solution of a continuous OU sample path: **the truth process in this package is linearly interpolated nodal OU**.

For the independent thrust check, let ρ=0 and T be constant. With y=a^(-1/2), dy/dt=-T/(m√μ). Since m=m0-Tt/(Isp g0),

    a(t)^(-1/2) = a0^(-1/2) + (Isp g0/√μ) ln[m(t)/m0].

This closed-form solution is compared with RK4. An independent SciPy DOP853 comparison is also performed for a prescribed thrust command and varying atmosphere. Agreement in these examples is not a convergence proof for every closed-loop switching schedule.

## 2. Random atmosphere and measurements

    b~N(0,σb²), constant throughout a run.
    du=-(u/τu)dt+√(2σu²/τu)dW.
    u0~N(0,σu²).

For r=exp(-h/τu), the exact OU node transition is

    u[k+1]=r u[k]+σu√(1-r²) ξ[k],  ξ independent N(0,1).

Var(u[k+1])=r²σu²+(1-r²)σu²=σu², and Cov(u[k],u[k+j])=σu²r^j. The contribution of b does not decay over long time lags. u is mean-reverting toward zero, whereas b is a constant bias; they represent different effects.

The marginal variance of η=b+u is .3²+.15²=.1125. The median of expη is 1 and its mean is exp(.1125/2)≈1.05786. A -.05625 shift to enforce unit mean **is not applied**. The exponential ensures positive density; a lognormal assumption is not evidence of physical atmospheric accuracy. Because of temporal correlation, the time average of one realization need not equal this marginal mean.

Measurements follow

    z=a+c+ε, ε~N(0,5²),
    dc=-(c/τc)dt+√(2σc²/τc)dVc, c0~N(0,σc²).

c is generated with the same OU transition form. The streams for b,u,c,ε are assumed independent. True a initially equals a0; the estimator's 75 m² prior uncertainty around a0 is a separate engineering assumption. Since the prior and actual initial-state distribution do not match exactly, filter consistency is not automatic.

## 3. Four-state extended estimator

    x=[a,b,u,c]^T,  h(x)=a+c, Hm=[1,0,0,1], R=25 m².
    x0=[a0,0,0,0], P0=diag(75,.09,.0225,25).

The same estimator operates throughout the mission for every policy. Colored sensor error is represented by a separate state rather than simply added to white-noise R. The local dynamics Jacobian is

    J = [α g g 0; 0 0 0 0; 0 0 -1/τu 0; 0 0 0 -1/τc]
    g=-G d
    α=(3G/2a)(T/m-d)-Gd(-1/H-1/a).

This follows from ∂d/∂a=d(-1/H-1/a) and ∂d/∂b=∂d/∂u=d. Cross-covariances among a,b,u are retained. Mass is treated as a known deterministic quantity; there is no separate uncertain mass state.

For locally frozen J, F=exp(Jh):

    F11=exp(αh), F12=g L(α,h),
    F13=g exp(-h/τu)L(α+1/τu,h),
    F22=1,F33=exp(-h/τu),F44=exp(-h/τc),
    L(q,h)=expm1(qh)/q; its limit as q→0 is h.

For small |qh|, the code uses L=h[1+qh/2+(qh)²/6+(qh)³/24], avoiding 0/0 and cancellation error. Other F entries are zero.

The continuous local process-noise intensity is D=diag(0,0,2σu²/τu,2σc²/τc), and Q=∫0^h exp(Js) D exp(Js)^T ds. The outer product of the column carrying u's influence into a is integrated with five-point Gauss–Legendre quadrature. The independent colored-error entry is exact: Q44=σc²[1-exp(-2h/τc)]. This Q belongs to the continuous local OU approximation; it is not exactly the covariance of the linearly interpolated truth process. Five-point quadrature is itself an approximation to the integral. The check compares it against an 8×8 Van Loan matrix exponential. Q is positive semidefinite; floating-point rounding may introduce extremely small negative eigenvalues.

The predicted mean propagates u and c using conditional exponential decay. It advances a by RK4 with u0, u0 exp(-h/(2τu)), u0 exp(-h/τu). The covariance update is P-=F P+ F^T+Q. This is a locally linearized EKF, not an exact Bayesian filter for the nonlinear system.

Measurement update:

    ν=z-Hm x-, S=Hm P- Hm^T+R, K=P- Hm^T/S,
    x+=x-+Kν,
    P+=(I-KHm)P-(I-KHm)^T+K R K^T.

The Joseph form is used for numerical symmetry/positive-semidefiniteness, followed by symmetrization (P+P^T)/2. S must be finite and positive. P11 is orbital variance; P22+2P23+P33 is log-drag-bias variance. Plotting ±1.96√P11 displays the filter's uncertainty claim; it cannot be called a calibrated 95% interval without measuring actual coverage.

## 4. Actuator state machine

Modes are 0 OFF,1 WARMUP,2 ON,3 COOLDOWN. **At most one transition occurs per node**; elseif ordering matters. The timer resets on a transition and increases by h after the interval. Initial mode is OFF with timer=minOFF, assuming the actuator has already rested.

OFF→WARMUP requires a request, timer≥minOFF, remaining open-window time≥warmup+minON, remaining mission time≥warmup+minON, and available power≥nominal power. WARMUP→ON requires timer≥warmup. Once warmup starts, withdrawing the request does not cancel it immediately. ON→COOLDOWN occurs when the request has been withdrawn and minON has elapsed, or when nominal power availability is lost. Losing availability before minON is an abort. COOLDOWN→OFF requires timer≥cooldown, after which minOFF must be waited separately. Even at low throttle, startup/continuation feasibility is checked conservatively against nominal 50 W.

Within each 5400 s period, the open window is [0,f×5400). Allocated electrical power is 80 W while open and zero otherwise. Rejecting a request because of constraints is not a power fault. If commanded P exceeds the allocation, T/P are set to zero, cooldown begins and power_fault is counted. Even zero-duration parameters can retain a one-node effect under the single-transition rule; do not interpret this as an exact continuous-event model.

## 5. Main-mission policies

**Periodic:** at the initial node and every 12 hours, Jcredit increases by d(a0,m0,0,ρ0) m0×43200×gain. Applied impulse T h is subtracted each interval; negative credit is retained. Positive credit produces a request. Minimum ON can cause overshoot of the impulse budget. The policy uses the nominal atmosphere, not the true bias. This fixed reference is not claimed to be optimized.

**Hysteresis:** the latch turns ON when estimated a-a0<-500 and OFF when estimated a-a0>300. It retains its previous state between the thresholds and requests Tmax while active.

**Drag-predictive hysteresis:** the activation signal is a_hat-G(a_hat)d_hat×900. This is a fixed short-term drag prediction; deactivation still uses a_hat-a0>300. Future true u is not read. This is neither optimal MPC nor probabilistically safe control.

## 6. Common 7-day settlement phase

Outside the final 5400 s of settlement,

    e=a_target + G d_hat (1-f) Pperiod - a_hat,
    request=(e>1 m),
    Twanted=clip[m(d_hat+max(e,0)/(G×1200)),Tmin,Tmax].

G d_hat (1-f)Pperiod is an approximate forward allowance for drag during the closed window. This is a prediction-based controller design choice, not a +1 km change to the target. The actual terminal target is read only from missions.json.

During the final 5400 s, three feasibility candidates are evaluated: request for as long as possible, request sufficient to meet minimum ON at the first feasible burn, and no new request. Existing mandatory burn/rest states are propagated through the same actuator state machine. For each candidate, a constant ON-thrust amplitude in [Tmin,Tmax] is fitted toward the terminal target using 14 bisection iterations; an endpoint is selected when the target lies outside that range. This uses the expectation that terminal a increases with throttle; there is no universal global-optimality proof. Future u conditionally decays toward zero and b remains constant.

Candidates first minimize predicted maximum service-band violation, then absolute terminal error. If both terminal errors are≤0.05 m, the candidate whose last ON slot is later is preferred. This rule neither minimizes fuel nor bounds risk probabilistically. The plan is recomputed at every node rather than committed unconditionally for the full horizon. Actual atmospheric deviations can cause terminal failures. Applying common settlement to every policy can reduce total-fuel differences, so main-mission and settlement consumption should also be analyzed separately.

## 7. Scope of the evidence

These derivations provide algebraic verification under the stated assumptions. Local linear F/Q formulas are not certificates for nonlinear/global uncertainty. Independent Python checks test selected numerical examples. MATLAB parity checks implementation agreement. Independent experiments assess statistical performance. Flight-data calibration assesses the physical model. These five levels are not interchangeable.
