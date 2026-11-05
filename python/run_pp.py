"""Development runner: saved inputs, isolated outputs, no implicit test-set access."""
import argparse,csv,hashlib,json,platform,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.io import savemat,loadmat
import pp_core as p
ROOT=Path(__file__).resolve().parents[1]
def integrity():
    m=json.loads((ROOT/'MANIFEST_SHA256.json').read_text())
    for e in m['files']:
        if hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()!=e['sha256']:raise RuntimeError('Changed package: '+e['path'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rq',choices=['RQ1','RQ2','both'],default='both');ap.add_argument('--mode',choices=['smoke','nominal','pilot'],default='smoke');ap.add_argument('--seed',type=int,default=72001);ap.add_argument('--out',type=Path,default=ROOT/'results');a=ap.parse_args();integrity()
    if not 72001<=a.seed<=72030:raise ValueError('Development seeds only: 72001..72030')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f');out=a.out/stamp;out.mkdir(parents=True,exist_ok=False)
    spec=p.load_spec();rqs=['RQ1','RQ2'] if a.rq=='both' else [a.rq];seeds=range(72001,72031) if a.mode=='pilot' else [a.seed]
    if a.mode=='smoke':spec.update(main_duration_days=.125,common_settlement_days=.0625,terminal_horizon_s=900.)
    masses=[25.,35.6,50.] if a.mode=='pilot' else [spec['mass_kg']];rhos=spec['density_cases'] if a.mode=='pilot' else [2e-11];fractions=[.6,.8,1.] if a.mode=='pilot' else [spec['available_fraction']]
    meta=dict(schema='PP-1.0',purpose='development only',mode=a.mode,python=sys.version,platform=platform.platform(),numpy=np.__version__,manifest_sha256=hashlib.sha256((ROOT/'MANIFEST_SHA256.json').read_bytes()).hexdigest(),spec=spec,missions=json.loads((ROOT/'config/missions.json').read_text()),seeds=list(seeds),masses=masses,rhos=rhos,fractions=fractions)
    (out/'run_metadata.json').write_text(json.dumps(meta,indent=2))
    with (out/'summary.csv').open('w',newline='') as fh:
        writer=csv.DictWriter(fh,fieldnames=['case','seed','mass_kg','available_fraction']+p.METRIC_NAMES+['rq','policy','rho0','terminal_target_offset_m','schema','status']);writer.writeheader()
        ci=0
        for mass in masses:
         for rho in rhos:
          for frac in fractions:
           c=dict(spec,mass_kg=mass,available_fraction=frac);p.validate(c);ci+=1
           for seed in seeds:
            f=p.forcing(c,seed);tag=f'case{ci:03d}_seed{seed}';folder=out/tag;folder.mkdir()
            savemat(folder/'shared_input.mat',dict(c=c,bias=f[0],u=f[1],white=f[2],colored=f[3],rho=rho,seed=seed),do_compression=True)
            for rq in rqs:
             for policy in p.POLICIES:
              result,trace=p.simulate(c,rq,policy,rho,f);writer.writerow(dict(case=ci,seed=seed,mass_kg=mass,available_fraction=frac,**result));fh.flush()
              np.savez_compressed(folder/f'{rq}_{policy}.npz',trace=trace,trace_names=p.TRACE_NAMES,result=json.dumps(result))
              print(tag,rq,policy,'qualified=',result['qualified'],'fuel_g=',round(result['fuel_g'],4),flush=True)
    print('Outputs:',out)
if __name__=='__main__':main()
