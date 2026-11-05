"""Developer-only fixture generation; never executed by the verifier.
Changing expected arrays requires a new package manifest and new MATLAB parity.
"""
from pathlib import Path
import json,time,hashlib
import numpy as np
from scipy.io import savemat
import pp_core as pp
ROOT=Path(__file__).resolve().parents[1]
def build(kind):
    s=pp.load_spec()
    if kind=='quick':s.update(main_duration_days=.125,common_settlement_days=.0625,terminal_horizon_s=900.)
    seed=73001 if kind=='quick' else 73002;f=pp.forcing(s,seed);rho=2e-11
    metrics=[];traces=np.empty((1,6),dtype=object);commands=np.empty((1,6),dtype=object);names=[];i=0;prefixes={}
    for rq in ['RQ1','RQ2']:
        for pol in pp.POLICIES:
            start=time.time();r,t=pp.simulate(s,rq,pol,rho,f);metrics.append([r[k] for k in pp.METRIC_NAMES]);names.append(rq+'/'+pol)
            inds=np.unique(np.r_[np.arange(0,len(t),10),len(t)-1]);traces[0,i]=t[inds];commands[0,i]=t[:,9:14]
            pre=t[t[:,0]<s['main_duration_days']*86400]
            if rq=='RQ1':prefixes[pol]=pre
            else:assert np.array_equal(prefixes[pol],pre),'RQ main prefix changed'
            print(kind,rq,pol,'seconds',round(time.time()-start,2),'qualified',r['qualified'],'terminal_m',round(r['terminal_error_m'],4),flush=True)
            i+=1
    path=ROOT/'fixtures'/('shared_'+kind+'.mat')
    savemat(path,dict(c=s,seed=seed,rho=rho,bias=f[0],u=f[1][:,None],white=f[2][:,None],colored=f[3][:,None],expected_metrics=np.array(metrics),expected_trace=traces,expected_commands=commands,sample_indices=(inds+1)[:,None],case_names=np.array(names,dtype=object)[None,:],metric_names=np.array(pp.METRIC_NAMES,dtype=object)[None,:],trace_names=np.array(pp.TRACE_NAMES,dtype=object)[None,:]),do_compression=True)
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),seed=seed,config=s,source='PP named PCG64 streams; saved arrays are authoritative',case_names=names,scope='implementation parity; development fixture, not independent performance evidence',runs=[dict(zip(pp.METRIC_NAMES,v)) for v in metrics])
if __name__=='__main__':
    records=[build(k) for k in ['quick','full']]
    (ROOT/'fixtures/fixture_ledger.json').write_text(json.dumps(records,indent=2)+'\n')
