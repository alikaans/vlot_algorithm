"""PP-1.0: common four-state, causal averaged-orbit research model.
No legacy project imports. cache=False avoids stale cross-module JIT caches.
"""
import json, math
from pathlib import Path
import numpy as np
try:
    from numba import njit
except ImportError:
    def njit(**kwargs):
        return lambda f: f

KEYS=['mu','g0','earth_radius_m','mass_kg','Isp_s','thrust_max_N','nominal_propulsion_power_W','throttle_min_fraction','mean_a0_m','main_duration_days','common_settlement_days','service_mean_a_halfband_m','terminal_tolerance_m','step_s','Cd','area_m2','scale_height_m','availability_period_s','available_fraction','propulsion_allocation_W','warmup_s','minimum_on_s','minimum_off_s','passive_cooldown_s','bias_sigma','ou_sigma','ou_tau_s','measurement_sigma_m','colored_sigma_m','colored_tau_s','lower_trigger_m','upper_trigger_m','predictive_horizon_s','settlement_response_s','terminal_deadband_m','terminal_horizon_s','terminal_root_iterations','terminal_numeric_tie_m','model_altitude_min_m','model_altitude_max_m','observer_prior_a_variance_m2','periodic_interval_s','periodic_impulse_gain']
(MU,G0,RE,M0,ISP,TMAX,PNOM,TMIN,A0,MAIN,SETTLE,BAND,TOL,DT,CD,AREA,H,PERIOD,FRAC,ALLOC,WARM,MINON,MINOFF,COOL,SIGB,SIGU,TAUU,SIGW,SIGC,TAUC,LOW,HIGH,HPRED,RESPONSE,DEADBAND,HORIZON,ROOTIT,TIE,DOMAINLO,DOMAINHI,PAA,PPERI,PG)=range(len(KEYS))
POLICIES=['periodic','hysteresis','predictive_hysteresis']
TRACE_NAMES=['time_s','a_offset_m','mass_kg','estimate_a_offset_m','estimate_b','estimate_u','estimate_colored_m','variance_a_m2','variance_eta','thrust_N','power_W','mode','timer_s','request','fuel_g','energy_Wh','actual_log_drag','measurement_m','innovation_m','innovation_variance_m2']+['P11','P12','P13','P14','P22','P23','P24','P33','P34','P44']
GN=np.array([-.906179845938664,-.538469310105683,0.,.538469310105683,.906179845938664])
GW=np.array([.236926885056189,.478628670499366,.568888888888889,.478628670499366,.236926885056189])

def load_spec(path=None):
    path=Path(path) if path else Path(__file__).resolve().parents[1]/'config/spec.json'
    s=json.loads(path.read_text());validate(s);return s

def validate(s):
    for k in KEYS:
        if k not in s or not isinstance(s[k],(int,float)) or not np.isfinite(s[k]):raise ValueError('Invalid '+k)
    positive=['mu','g0','earth_radius_m','mass_kg','Isp_s','thrust_max_N','nominal_propulsion_power_W','mean_a0_m','service_mean_a_halfband_m','terminal_tolerance_m','step_s','Cd','area_m2','scale_height_m','availability_period_s','ou_tau_s','measurement_sigma_m','colored_tau_s','settlement_response_s','terminal_horizon_s','observer_prior_a_variance_m2','periodic_interval_s']
    for k in positive:
        if s[k]<=0:raise ValueError('Positive '+k)
    for k in ['main_duration_days','common_settlement_days','warmup_s','minimum_on_s','minimum_off_s','passive_cooldown_s','bias_sigma','ou_sigma','colored_sigma_m','predictive_horizon_s','terminal_deadband_m','periodic_impulse_gain','propulsion_allocation_W','terminal_numeric_tie_m']:
        if s[k]<0:raise ValueError('Nonnegative '+k)
    if not 0<s['available_fraction']<=1 or not 0<s['throttle_min_fraction']<=1:raise ValueError('Invalid fraction')
    if s['lower_trigger_m']>=s['upper_trigger_m']:raise ValueError('Invalid triggers')
    if s.get('initial_offset_m',0)!=0:raise ValueError('PP requires reference=start orbit')
    if not s['model_altitude_min_m']<s['mean_a0_m']-s['earth_radius_m']<s['model_altitude_max_m']:raise ValueError('Initial domain')
    dt=s['step_s'];end=(s['main_duration_days']+s['common_settlement_days'])*86400
    for v in [end,s['main_duration_days']*86400,s['availability_period_s'],s['available_fraction']*s['availability_period_s'],s['warmup_s'],s['minimum_on_s'],s['minimum_off_s'],s['passive_cooldown_s'],s['periodic_interval_s'],s['terminal_horizon_s']]:
        if abs(v/dt-round(v/dt))>1e-8:raise ValueError('Grid alignment')
    if end<dt or int(s['terminal_root_iterations'])!=s['terminal_root_iterations'] or not 1<=s['terminal_root_iterations']<=40:raise ValueError('Duration/root iterations')

def mission_target(rq):
    if rq not in ['RQ1','RQ2']:raise ValueError('RQ1/RQ2 required')
    return float(json.loads((Path(__file__).resolve().parents[1]/'config/missions.json').read_text())[rq]['target_offset_m'])

def params(s):return np.array([s[k] for k in KEYS],dtype=float)

def forcing(s,seed,deterministic=False):
    """Independent named PCG64 streams; preserved prefixes when duration changes."""
    if not isinstance(seed,(int,np.integer)) or not 0<=seed<=2**32-1:raise ValueError('uint32 seed required')
    n=round((s['main_duration_days']+s['common_settlement_days'])*86400/s['step_s'])+1
    streams=[np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed),i]))) for i in range(4)]
    b=s['bias_sigma']*streams[0].standard_normal()
    def ar(gen,sigma,tau):
        eps=gen.standard_normal(n);a=np.empty(n);a[0]=sigma*eps[0];ph=math.exp(-s['step_s']/tau)
        for k in range(1,n):a[k]=ph*a[k-1]+sigma*math.sqrt(-math.expm1(-2*s['step_s']/tau))*eps[k]
        return a
    u=ar(streams[1],s['ou_sigma'],s['ou_tau_s']);w=streams[2].standard_normal(n)*s['measurement_sigma_m'];colored=ar(streams[3],s['colored_sigma_m'],s['colored_tau_s'])
    if deterministic:b=0.;u[:]=0;w[:]=0;colored[:]=0
    return b,u,w,colored

@njit(cache=False)
def drag(a,m,eta,rho,c):return .5*rho*math.exp(-(a-c[A0])/c[H]+eta)*c[CD]*c[AREA]*c[MU]/a/m
@njit(cache=False)
def rhs(a,m,eta,T,rho,c):return 2*math.sqrt(a**3/c[MU])*(T/m-drag(a,m,eta,rho,c))
@njit(cache=False)
def plant(a,m,T,e0,em,e1,rho,h,c):
    dm=-T/(c[ISP]*c[G0]);k1=rhs(a,m,e0,T,rho,c)
    k2=rhs(a+h*k1/2,m+h*dm/2,em,T,rho,c);k3=rhs(a+h*k2/2,m+h*dm/2,em,T,rho,c)
    k4=rhs(a+h*k3,m+h*dm,e1,T,rho,c)
    return a+h*(k1+2*k2+2*k3+k4)/6,m+h*dm
@njit(cache=False)
def divided_exp(alpha,h):
    if abs(alpha*h)<1e-8:return h*(1+alpha*h/2+(alpha*h)**2/6+(alpha*h)**3/24)
    return math.expm1(alpha*h)/alpha
@njit(cache=False)
def phi(alpha,g,h,c):
    F=np.zeros((4,4));eu=math.exp(-h/c[TAUU]);F[0,0]=math.exp(alpha*h);F[0,1]=g*divided_exp(alpha,h)
    F[0,2]=g*eu*divided_exp(alpha+1/c[TAUU],h);F[1,1]=1;F[2,2]=eu;F[3,3]=math.exp(-h/c[TAUC]);return F
@njit(cache=False)
def observer_predict(x,P,m,T,rho,c):
    h=c[DT];a=x[0];gain=2*math.sqrt(a**3/c[MU]);d=drag(a,m,x[1]+x[2],rho,c)
    alpha=1.5*gain/a*(T/m-d)-gain*d*(-1/c[H]-1/a);g=-gain*d
    F=phi(alpha,g,h,c);Q=np.zeros((4,4));qu=2*c[SIGU]**2/c[TAUU]
    for k in range(5):
        M=phi(alpha,g,h*(GN[k]+1)/2,c);v=M[:,2]
        Q+=h*GW[k]/2*qu*np.outer(v,v)
    Q[3,3]=c[SIGC]**2*(-math.expm1(-2*h/c[TAUC]))
    uh=x[2]*math.exp(-h/(2*c[TAUU]));ue=x[2]*math.exp(-h/c[TAUU])
    aa,_=plant(a,m,T,x[1]+x[2],x[1]+uh,x[1]+ue,rho,h,c)
    xp=np.array([aa,x[1],ue,x[3]*math.exp(-h/c[TAUC])]);pp=F@P@F.T+Q
    return xp,(pp+pp.T)/2,F,Q
@njit(cache=False)
def observer_update(x,P,z,c):
    R=c[SIGW]**2;ph=P[:,0]+P[:,3];S=P[0,0]+2*P[0,3]+P[3,3]+R
    
    if not np.isfinite(S) or S<=0:raise ValueError('Nonpositive innovation covariance')
    K=ph/S;innov=z-x[0]-x[3];xn=x+K*innov;M=np.eye(4);M[:,0]-=K;M[:,3]-=K
    pn=M@P@M.T+R*np.outer(K,K);return xn,(pn+pn.T)/2,innov,S
@njit(cache=False)
def actuator(mode,timer,request,Twanted,t,end,c):
    remaining=c[FRAC]*c[PERIOD]-t%c[PERIOD];cap=c[ALLOC] if remaining>0 else 0.;abort=0
    if mode==0 and request and timer>=c[MINOFF] and remaining>=c[WARM]+c[MINON] and end-t>=c[WARM]+c[MINON] and cap>=c[PNOM]:mode=1;timer=0.
    elif mode==1 and timer>=c[WARM]:mode=2;timer=0.
    elif mode==2 and ((not request and timer>=c[MINON]) or cap<c[PNOM]):
        if timer<c[MINON]:abort=1
        mode=3;timer=0.
    elif mode==3 and timer>=c[COOL]:mode=0;timer=0.
    T=0.;P=0.
    if mode==1:P=c[PNOM]
    if mode==2:T=min(max(Twanted,c[TMIN]*c[TMAX]),c[TMAX]);P=c[PNOM]*T/c[TMAX]
    fault=0
    if P>cap+1e-12:T=0.;P=0.;mode=3;timer=0.;fault=1
    return mode,timer,T,P,abort,fault
@njit(cache=False)
def schedule(t,end,mode,timer,stop,c):
    count=int(round((end-t)/c[DT]));on=np.zeros(count,np.uint8);first=-1;last=-1
    for k in range(count):
        tt=t+k*c[DT];mode,timer,T,_,_,_=actuator(mode,timer,tt<stop,c[TMAX],tt,end,c)
        if T>0:
            on[k]=1;last=k
            if first<0:first=k
        timer+=c[DT]
    return on,first,last
@njit(cache=False)
def forecast(x,m,T,on,rho,c):
    a=x[0];u=x[2];peak=max(abs(a-c[A0])-c[BAND],0.);h=c[DT]
    for k in range(len(on)):
        force=T if on[k] else 0.;um=u*math.exp(-h/(2*c[TAUU]));ue=u*math.exp(-h/c[TAUU])
        a,m=plant(a,m,force,x[1]+u,x[1]+um,x[1]+ue,rho,h,c);u=ue
        peak=max(peak,abs(a-c[A0])-c[BAND])
    return a,peak
@njit(cache=False)
def fit_thrust(x,m,on,rho,target,c):
    low=c[TMIN]*c[TMAX];high=c[TMAX];al,vl=forecast(x,m,low,on,rho,c);ah,vh=forecast(x,m,high,on,rho,c)
    if al>=target:return low,al,vl
    if ah<=target:return high,ah,vh
    for _ in range(int(c[ROOTIT])):
        mid=(low+high)/2;am,_=forecast(x,m,mid,on,rho,c)
        if am<target:low=mid
        else:high=mid
    T=(low+high)/2;af,v=forecast(x,m,T,on,rho,c);return T,af,v
@njit(cache=False)
def terminal_plan(x,m,rho,t,end,mode,timer,target,c):
    _,first,_=schedule(t,end,mode,timer,end,c);minstop=t
    if first>=0:
        needed=max(c[MINON]-timer,c[DT]) if mode==2 and first==0 else c[MINON]
        minstop=t+first*c[DT]+needed
    stops=np.array([end,minstop,t]);bestV=1e99;bestE=1e99;bestLast=-1;bestT=c[TMIN]*c[TMAX];bestR=False
    for k in range(3):
        slots,_,last=schedule(t,end,mode,timer,stops[k],c);T,af,v=fit_thrust(x,m,slots,rho,target,c);err=abs(af-target)
        better=v<bestV
        if v==bestV:
            if err<=c[TIE] and bestE<=c[TIE]:better=last>bestLast
            elif err<=c[TIE]:better=True
            elif bestE<=c[TIE]:better=False
            else:better=err<bestE
        if better:bestV=v;bestE=err;bestLast=last;bestT=T;bestR=t<stops[k]
    return bestR,bestT

@njit(cache=False)
def simulate_core(c,policy,rho,target_offset,b,u,white,colored):
    h=c[DT];main=c[MAIN]*86400;end=(c[MAIN]+c[SETTLE])*86400;N=int(round(end/h));target=c[A0]+target_offset
    trace=np.zeros((N+1,30));a=c[A0];m=c[M0];x=np.array([c[A0],0.,0.,0.]);P=np.diag(np.array([c[PAA],c[SIGB]**2,c[SIGU]**2,c[SIGC]**2]))
    mode=0;timer=c[MINOFF];latch=False;credit=0.;fuel=0.;energy=0.;maxvio=0.;viotime=0.;mainvio=0.;powerfault=0;aborts=0;complete=1;last=0
    for k in range(N+1):
        t=k*h;z=a+white[k]+colored[k];x,P,innov,S=observer_update(x,P,z,c)
        trace[k,:20]=np.array([t,a-c[A0],m,x[0]-c[A0],x[1],x[2],x[3],P[0,0],P[1,1]+2*P[1,2]+P[2,2],0.,0.,float(mode),timer,0.,fuel*1000,energy/3600,b+u[k],z,innov,S])
        trace[k,20:]=np.array([P[0,0],P[0,1],P[0,2],P[0,3],P[1,1],P[1,2],P[1,3],P[2,2],P[2,3],P[3,3]])
        if k==N:break
        if not np.isfinite(x).all() or not np.isfinite(P).all() or m<=0 or a-c[RE]<c[DOMAINLO] or a-c[RE]>c[DOMAINHI]:complete=0;break
        if t>=main:
            if end-t<=c[HORIZON]:request,Twanted=terminal_plan(x,m,rho,t,end,mode,timer,target,c)
            else:
                gain=2*math.sqrt(x[0]**3/c[MU]);dhat=drag(x[0],m,x[1]+x[2],rho,c)
                err=target+gain*dhat*(1-c[FRAC])*c[PERIOD]-x[0];request=err>c[DEADBAND]
                Twanted=min(max(m*(dhat+max(err,0)/(gain*c[RESPONSE])),c[TMIN]*c[TMAX]),c[TMAX])
        elif policy==0:
            if k%int(round(c[PPERI]/h))==0:credit+=drag(c[A0],c[M0],0.,rho,c)*c[M0]*c[PPERI]*c[PG]
            request=credit>0;Twanted=c[TMAX]
        else:
            signal=x[0]
            if policy==2:signal-=2*math.sqrt(x[0]**3/c[MU])*drag(x[0],m,x[1]+x[2],rho,c)*c[HPRED]
            if signal<c[A0]+c[LOW]:latch=True
            if x[0]>c[A0]+c[HIGH]:latch=False
            request=latch;Twanted=c[TMAX]
        mode,timer,T,power,ab,fl=actuator(mode,timer,request,Twanted,t,end,c);aborts+=ab;powerfault+=fl
        trace[k,9]=T;trace[k,10]=power;trace[k,11]=mode;trace[k,12]=timer;trace[k,13]=(1. if request else 0.)
        a,m=plant(a,m,T,b+u[k],b+(u[k]+u[k+1])/2,b+u[k+1],rho,h,c)
        fuel+=T*h/(c[ISP]*c[G0]);energy+=power*h;timer+=h;last=k+1
        if policy==0 and t<main:credit-=T*h
        vio=max(abs(a-c[A0])-c[BAND],0.);maxvio=max(maxvio,vio)
        if vio>0:viotime+=h
        if t<main:mainvio=max(mainvio,vio)
        x,P,_,_=observer_predict(x,P,m+T*h/(c[ISP]*c[G0]),T,rho,c)
    if last!=N or not np.isfinite(a) or not np.isfinite(m) or not np.isfinite(trace[:last+1]).all() or not np.isfinite(P).all() or m<=0 or not c[DOMAINLO]<=a-c[RE]<=c[DOMAINHI]:complete=0
    error=a-target;masserr=abs((c[M0]-m)-fuel)
    service=complete==1 and maxvio==0;terminal=complete==1 and abs(error)<=c[TOL];resource=powerfault==0 and aborts==0 and masserr<1e-8
    metrics=np.array([float(complete),(1. if service else 0.),(1. if terminal else 0.),(1. if resource else 0.),(1. if service and terminal and resource else 0.),1000*(c[M0]-m),energy/3600,error,a-c[A0],maxvio,viotime,mainvio,float(powerfault),float(aborts),masserr,last*h])
    return metrics,trace[:last+1]
METRIC_NAMES=['completed','service_pass','terminal_pass','resource_pass','qualified','fuel_g','energy_Wh','terminal_error_m','terminal_offset_m','max_violation_m','violation_duration_s','main_max_violation_m','power_faults','minimum_on_aborts','mass_account_error_kg','last_time_s']

def simulate(s,rq,policy,rho,f):
    validate(s)
    if rq not in ['RQ1','RQ2']:raise ValueError('RQ1 or RQ2 required')
    p=POLICIES.index(policy);target=mission_target(rq)
    n=round((s['main_duration_days']+s['common_settlement_days'])*86400/s['step_s'])+1
    b,u,w,col=f
    if any(len(v)!=n or not np.isfinite(v).all() for v in [u,w,col]) or not np.isfinite(b):raise ValueError('Forcing shape/values')
    if not np.isfinite(rho) or rho<=0:raise ValueError('Positive rho')
    m,t=simulate_core(params(s),p,rho,target,b,u,w,col)
    result=dict(zip(METRIC_NAMES,m.tolist()));result.update(rq=rq,policy=policy,rho0=rho,terminal_target_offset_m=target,schema=s['schema'],status='completed' if result['completed'] else 'invalid_or_domain_exit')
    return result,t
