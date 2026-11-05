"""Optional non-JIT execution check against the immutable quick fixture."""
import sys
sys.modules['numba']=None
import json,hashlib,time
from pathlib import Path
import numpy as np
from scipy.io import loadmat
import pp_core as p
r=Path(__file__).resolve().parents[1];d=loadmat(r/'fixtures/shared_quick.mat',simplify_cells=True);f=(float(d['bias']),d['u'],d['white'],d['colored']);inds=d['sample_indices'].astype(int)-1;tol=json.loads((r/'config/tolerances.json').read_text());checks=[];start=time.time()
for rq,i in [('RQ1',1),('RQ2',4)]:
 result,t=p.simulate(d['c'],rq,'hysteresis',float(d['rho']),f);err=abs(t[inds]-d['expected_trace'][i]);cmd=abs(t[:,9:14]-d['expected_commands'][i]);met=abs(np.array([result[k] for k in p.METRIC_NAMES])-d['expected_metrics'][i]);ok=np.all(err<=tol['trace_absolute']) and np.all(cmd<=tol['commands_absolute']) and np.all(met<=tol['metrics_absolute']);assert ok
 checks.append(dict(rq=rq,passed=bool(ok),max_state_error=float(err.max()),max_command_error=float(cmd.max()),max_metric_error=float(met.max())));print(checks[-1],flush=True)
report=dict(passed=True,scope='Non-JIT vs delivered JIT examples; same algorithm, not independent physics',elapsed_s=time.time()-start,source_sha256=hashlib.sha256((r/'python/pp_core.py').read_bytes()).hexdigest(),checks=checks)
(r/'validation/local_interpreter.json').write_text(json.dumps(report,indent=2)+'\n')
