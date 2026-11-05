from pathlib import Path
import numpy as np,json
from scipy.io import savemat
import pp_core as p
r=Path(__file__).resolve().parents[1];s=p.load_spec();c=p.params(s)
edges=[];answers=[]
for mode in range(4):
 for timer in [0.,30.,570.,600.,870.,900.,1200.,1800.]:
  for t in [0.,600.,1740.,3240.,5370.]:
   for request in [0,1]:
    for T in [.000055,.00055]:
     args=[mode,timer,request,T,t,86400.];edges.append(args);answers.append(p.actuator(*args,c))
maths=[]
for rho in [1e-11,2e-11,8e-11]:
 for h in [15.,30.,60.]:
  cc=c.copy();cc[p.DT]=h;x=np.array([s['mean_a0_m']+100,.1,-.05,2.]);P=np.diag([75.,.09,.0225,25.]);m=35.59;T=.0003
  xp,pp,F,Q=p.observer_predict(x,P,m,T,rho,cc);xn,pn,innov,S=p.observer_update(xp,pp,s['mean_a0_m']+105,cc)
  maths.append(dict(x=x,P=P,m=m,T=T,rho=rho,h=h,xp=xp,pp=pp,F=F,Q=Q,z=s['mean_a0_m']+105,xn=xn,pn=pn,innov=innov,S=S))
savemat(r/'fixtures/components.mat',dict(c=s,edges_input=np.array(edges),edges_expected=np.array(answers),math_probes=np.array(maths,dtype=object)),do_compression=True)
(r/'fixtures/component_ledger.json').write_text(json.dumps(dict(actuator_examples=len(edges),math_probes=len(maths),scope='Cross-language examples; independent mathematical checks are in validate_python.py'),indent=2)+'\n')
print(len(edges),'actuator examples;',len(maths),'observer probes')
