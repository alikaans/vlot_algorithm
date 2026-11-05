function f=pp_make_forcing(c,seed)
% Native exploratory RNG; not a Python PCG64 replay. Caller RNG restored.
c=pp_numeric_spec(c);validateattributes(seed,{'numeric'},{'scalar','integer','finite','>=',0,'<=',2^32-1});pp_validate(c);
old=rng;cleanup=onCleanup(@() rng(old)); %#ok<NASGU>
rng(double(seed),'twister');N=round((c.main_duration_days+c.common_settlement_days)*86400/c.step_s)+1;
f=struct('bias',c.bias_sigma*randn,'u',ar(N,c.ou_sigma,c.ou_tau_s,c.step_s),'white',[],'colored',[]);
f.white=c.measurement_sigma_m*randn(N,1);f.colored=ar(N,c.colored_sigma_m,c.colored_tau_s,c.step_s);
f.source='MATLAB native twister/randn: not Python seed parity';f.seed=seed;
end
function a=ar(N,sigma,tau,dt)
a=zeros(N,1);a(1)=sigma*randn;ph=exp(-dt/tau);sd=sigma*sqrt(-expm1(-2*dt/tau));
for j=2:N,a(j)=ph*a(j-1)+sd*randn;end
end
