function report=pp_type_selftest()
%PP_TYPE_SELFTEST Same-valued integer/double inputs must yield identical traces.
c=pp_load_spec();c.main_duration_days=0;c.common_settlement_days=1/16;c.terminal_horizon_s=900;
ci=c;names={'main_duration_days','step_s','warmup_s','minimum_on_s','terminal_root_iterations'};
for k=1:numel(names),name=names{k};ci.(name)=int64(ci.(name));end
cn=pp_numeric_spec(ci);
for k=1:numel(names),assert(isa(cn.(names{k}),'double'),'PP:TypeTest','Parameter normalization failed');end
N=round((c.main_duration_days+c.common_settlement_days)*86400/c.step_s);
f=struct('bias',0,'u',zeros(N+1,1),'white',zeros(N+1,1),'colored',zeros(N+1,1));
[r,tr]=pp_simulate(c,'RQ1','hysteresis',2e-11,f);
[ri,tri]=pp_simulate(ci,'RQ1','hysteresis',2e-11,f);
assert(isequaln(r,ri)&&isequaln(tr,tri),'PP:TypeTest','Equal-valued numeric types changed simulation');
assert(isa(tri,'double')&&tri(1,3)==c.mass_kg&&tri(1,9)>0,'PP:TypeTest','Fractional trace values lost');
report=struct('passed',true,'duration_s',N*c.step_s,'input_types',{{'double','int64'}},'scope','Input type invariance, not physical validation');
end
