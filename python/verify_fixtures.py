"""Read-only replay against the delivered expected arrays; never regenerates them."""
from pathlib import Path
import hashlib,json,sys,platform
import numpy as np
from scipy.io import loadmat
import pp_core as p
ROOT=Path(__file__).resolve().parents[1]
def verify():
    tol=json.loads((ROOT/'config/tolerances.json').read_text());checks=[]
    for kind in ['quick','full']:
        d=loadmat(ROOT/f'fixtures/shared_{kind}.mat',simplify_cells=True);s=d['c'];f=(float(d['bias']),d['u'],d['white'],d['colored']);inds=np.asarray(d['sample_indices'],int)-1
        for i,(rq,policy) in enumerate((rq,pol) for rq in ['RQ1','RQ2'] for pol in p.POLICIES):
            r,t=p.simulate(s,rq,policy,float(d['rho']),f)
            arrays=[(t[inds],d['expected_trace'][i],tol['trace_absolute']), (t[:,9:14],d['expected_commands'][i],tol['commands_absolute']), (np.array([r[k] for k in p.METRIC_NAMES]),d['expected_metrics'][i],tol['metrics_absolute'])]
            differences=[]
            for actual,expected,threshold in arrays:
                assert actual.shape==expected.shape
                dif=np.abs(actual-expected);assert np.isfinite(dif).all() and np.all(dif<=np.array(threshold)),(kind,rq,policy,float(dif.max()))
                differences.append(float(dif.max()))
            checks.append(dict(fixture=kind,rq=rq,policy=policy,passed=True,max_abs_state_command_metric=differences));print(kind,rq,policy,'PASS',differences,flush=True)
    return dict(passed=True,scope='Python replay only; MATLAB parity remains pending',checks=checks,python=sys.version,platform=platform.platform(),source_sha256=hashlib.sha256((ROOT/'python/pp_core.py').read_bytes()).hexdigest())
if __name__=='__main__':
    result=verify();(ROOT/'validation/local_python_fixture_replay.json').write_text(json.dumps(result,indent=2)+'\n')
