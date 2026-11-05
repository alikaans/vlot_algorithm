"""Independent mathematical/numerical checks. Never fit a controller here."""
import json,math,time
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import expm
import pp_core as pp

def validate_all():
    s=pp.load_spec();c=pp.params(s);checks=[]
    def check(name,ok,detail):
        checks.append(dict(name=name,passed=bool(ok),detail=detail))
        if not ok:raise AssertionError(name+': '+str(detail))
    # Exact invariants, no atmospheric / thrust perturbation.
    a,m=pp.plant(c[pp.A0],c[pp.M0],0.,0.,0.,0.,0.,1000.,c)
    check('two_body_mean_invariant',a==c[pp.A0] and m==c[pp.M0],dict(a=a,m=m))
    # Analytic finite-thrust, variable-mass circular-energy solution.
    a=c[pp.A0];m=c[pp.M0];T=c[pp.TMAX];duration=7200.
    for _ in range(int(duration/30)):a,m=pp.plant(a,m,T,0.,0.,0.,0.,30.,c)
    exact=1/(1/math.sqrt(c[pp.A0])-c[pp.ISP]*c[pp.G0]/math.sqrt(c[pp.MU])*math.log(c[pp.M0]/m))**2
    check('analytic_thrust_mass_solution',abs(a-exact)<1e-5 and abs(m-(c[pp.M0]-T*duration/(c[pp.ISP]*c[pp.G0])))<1e-10,dict(a_error_m=a-exact))
    # Independent adaptive ODE integration, same prescribed forcing.
    rho=4e-11;eta=.2;duration=7200.;T=c[pp.TMAX]*.4
    def independent_rhs(t,z):
        aa,mm=z;F=.5*rho*np.exp(-(aa-c[pp.A0])/c[pp.H]+eta)*c[pp.CD]*c[pp.AREA]*c[pp.MU]/aa
        return [2*np.sqrt(aa**3/c[pp.MU])*(T-F)/mm,-T/(c[pp.ISP]*c[pp.G0])]
    oracle=solve_ivp(independent_rhs,[0,duration],[c[pp.A0],c[pp.M0]],method='DOP853',rtol=2.3e-14,atol=[1e-8,1e-13]).y[:,-1]
    errors=[]
    for h in [60.,30.,15.]:
        aa=c[pp.A0];mm=c[pp.M0]
        for _ in range(int(duration/h)):aa,mm=pp.plant(aa,mm,T,eta,eta,eta,rho,h,c)
        errors.append(abs(aa-oracle[0]))
    check('DOP853_prescribed_force',max(errors)<1e-4,dict(step_s=[60,30,15],a_errors_m=errors))
    # Phi/Q compare against independent 8x8 Van Loan matrix exponential.
    worstF=0.;worstQ=0.;mineig=1.
    for alpha in [-1e-6,0.,2e-6]:
        for h in [15.,30.,60.]:
            cc=c.copy();cc[pp.DT]=h;x=np.array([c[pp.A0],.1,-.05,0.]);P=np.eye(4)
            gain=2*np.sqrt(x[0]**3/c[pp.MU]);d=pp.drag(x[0],c[pp.M0],.05,rho,c);g=-gain*d
            F=pp.phi(alpha,g,h,c);Q=np.zeros((4,4))
            for gn,gw in zip(pp.GN,pp.GW):
                M=pp.phi(alpha,g,h*(gn+1)/2,c);Q+=h*gw/2*(2*c[pp.SIGU]**2/c[pp.TAUU])*np.outer(M[:,2],M[:,2])
            Q[3,3]=c[pp.SIGC]**2*(-np.expm1(-2*h/c[pp.TAUC]))
            A=np.array([[alpha,g,g,0],[0,0,0,0],[0,0,-1/c[pp.TAUU],0],[0,0,0,-1/c[pp.TAUC]]])
            L=np.diag([0.,0.,2*c[pp.SIGU]**2/c[pp.TAUU],2*c[pp.SIGC]**2/c[pp.TAUC]])
            E=expm(np.block([[A,L],[np.zeros((4,4)),-A.T]])*h);Fref=E[:4,:4];Qref=E[:4,4:]@Fref.T
            worstF=max(worstF,float(np.max(abs(F-Fref))));worstQ=max(worstQ,float(np.max(abs(Q-Qref))));mineig=min(mineig,float(np.linalg.eigvalsh(Q).min()))
    check('Van_Loan_covariance',worstF<1e-10 and worstQ<1e-10 and mineig>=-1e-12,dict(phi_max_abs=worstF,Q_max_abs=worstQ,Q_min_eigenvalue=mineig))
    # Jacobian derivatives against numerical finite differences.
    x=np.array([c[pp.A0],.1,-.05,0.]);gain=2*np.sqrt(x[0]**3/c[pp.MU]);d=pp.drag(x[0],c[pp.M0],x[1]+x[2],rho,c)
    alpha=1.5*gain/x[0]*(T/c[pp.M0]-d)-gain*d*(-1/c[pp.H]-1/x[0]);g=-gain*d
    numerical_a=(pp.rhs(x[0]+.1,c[pp.M0],.05,T,rho,c)-pp.rhs(x[0]-.1,c[pp.M0],.05,T,rho,c))/.2
    numerical_eta=(pp.rhs(x[0],c[pp.M0],.05+1e-5,T,rho,c)-pp.rhs(x[0],c[pp.M0],.05-1e-5,T,rho,c))/2e-5
    check('Jacobian_finite_difference',abs(alpha-numerical_a)<1e-10 and abs(g-numerical_eta)<1e-9,dict(a_error=alpha-numerical_a,eta_error=g-numerical_eta))
    # Closed-form scalar Gaussian conditioning vs generic matrix implementation.
    P=np.array([[75.,.1,.02,1.],[.1,.09,0.,0.],[.02,0.,.0225,0.],[1.,0.,0.,25.]])
    H=np.array([[1.,0.,0.,1.]]);x=np.array([c[pp.A0],0.,0.,0.]);z=x[0]+3.
    xn,pn,_,_=pp.observer_update(x,P,z,c);K=P@H.T@np.linalg.inv(H@P@H.T+25)
    expected=P-P@H.T@np.linalg.inv(H@P@H.T+25)@H@P
    check('Joseph_conditioning',np.max(abs(pn-expected))<1e-12 and np.linalg.eigvalsh(pn).min()>0,dict(max_abs=float(np.max(abs(pn-expected)))))
    # Hand-calculated actuator boundary examples.
    finish=86400.
    examples=[((0,1800,True,c[pp.TMAX],0,finish),(1,0,0,50,0,0)),((1,600,True,c[pp.TMAX],600,finish),(2,0,c[pp.TMAX],50,0,0)),((2,870,False,c[pp.TMAX],1500,finish),(2,870,c[pp.TMAX],50,0,0)),((2,900,False,c[pp.TMAX],1500,finish),(3,0,0,0,0,0)),((3,1200,False,c[pp.TMAX],5000,finish),(0,0,0,0,0,0)),((0,1800,True,c[pp.TMAX],1800,finish),(0,1800,0,0,0,0)),((2,900,True,c[pp.TMAX],3240,finish),(3,0,0,0,0,0))]
    for i,(args,want) in enumerate(examples):check('actuator_boundary_'+str(i),np.allclose(pp.actuator(*args,c),want,rtol=0,atol=1e-14),{})
    short=dict(s,main_duration_days=.125,common_settlement_days=.0625,terminal_horizon_s=900.)
    f=pp.forcing(short,71001);f2=pp.forcing(short,71001)
    check('forcing_repeat',all(np.array_equal(a,b) for a,b in zip(f,f2)),{})
    longer=dict(short,common_settlement_days=.125);fl=pp.forcing(longer,71001)
    check('forcing_prefix',f[0]==fl[0] and all(np.array_equal(a,b[:len(a)]) for a,b in zip(f[1:],fl[1:])),{})
    r1,t1=pp.simulate(short,'RQ1','hysteresis',2e-11,f);r2,t2=pp.simulate(short,'RQ2','hysteresis',2e-11,f)
    before=t1[:,0]<short['main_duration_days']*86400
    check('RQ_main_command_prefix',np.array_equal(t1[before],t2[before]),{})
    check('RQ_target_use',np.any(t1[:,9]!=t2[:,9]) and r1['terminal_target_offset_m']==0 and r2['terminal_target_offset_m']==950,dict(RQ1_error_m=r1['terminal_error_m'],RQ2_error_m=r2['terminal_error_m']))
    fu=tuple(v.copy() if hasattr(v,'copy') else v for v in f);fu[1][400:]+=.4;fu[2][400:]+=30;fu[3][400:]-=10
    _,changed=pp.simulate(short,'RQ1','hysteresis',2e-11,fu)
    check('no_future_truth_leak',np.array_equal(t1[:400],changed[:400]),{})
    check('mass_energy_account',r1['mass_account_error_kg']<1e-8 and abs(np.sum(t1[:-1,10])*short['step_s']/3600-r1['energy_Wh'])<1e-8,dict(mass_error_kg=r1['mass_account_error_kg']))
    for spec in [dict(short,step_s=17),dict(short,available_fraction=1.1),dict(short,initial_offset_m=1)]:
        failed=False
        try:pp.validate(spec)
        except ValueError:failed=True
        check('reject_invalid_'+str(len(checks)),failed,{})
    return dict(schema='PP-1.0',passed=all(x['passed'] for x in checks),checks=checks,scope='Python numerical/unit checks only; not MATLAB parity or physical validation')
if __name__=='__main__':
    t=time.time();out=validate_all();out['elapsed_s']=time.time()-t
    import hashlib,sys,platform
    root=Path(__file__).resolve().parents[1]
    out['python']=sys.version;out['platform']=platform.platform()
    out['source_sha256']={str(q.relative_to(root)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [root/'python/pp_core.py',Path(__file__).resolve(),root/'config/spec.json',root/'config/missions.json']}
    p=Path(__file__).resolve().parents[1]/'validation/local_python_validation.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
