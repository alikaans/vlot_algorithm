function [result,trace]=pp_simulate(c,rq,policy,rho,f,progress)
%PP_SIMULATE PP-1.0. Final measurement affects diagnostics, never a command.
if nargin<6,progress=[];end
c=pp_numeric_spec(c);pp_validate(c);policies={'periodic','hysteresis','predictive_hysteresis'};ip=find(strcmp(policy,policies),1)-1;
assert(~isempty(ip),'PP:Policy','Unknown policy');assert(any(strcmp(rq,{'RQ1','RQ2'})),'PP:RQ','RQ1/RQ2 required');
validateattributes(rho,{'numeric'},{'scalar','finite','positive'});
targetOffset=pp_mission_target(rq);
target=c.mean_a0_m+targetOffset;h=c.step_s;main=c.main_duration_days*86400;finish=(c.main_duration_days+c.common_settlement_days)*86400;N=round(finish/h);
for field={'u','white','colored'},v=f.(field{1});assert(numel(v)==N+1&&all(isfinite(v(:))),'PP:Forcing','Forcing shape/values');end
assert(isscalar(f.bias)&&isfinite(f.bias),'PP:Forcing','Invalid bias');
a=c.mean_a0_m;m=c.mass_kg;x=[a;0;0;0];P=diag([c.observer_prior_a_variance_m2,c.bias_sigma^2,c.ou_sigma^2,c.colored_sigma_m^2]);
mode=0;timer=c.minimum_off_s;latch=false;credit=0;fuel=0;energy=0;maxvio=0;viotime=0;mainvio=0;powerfault=0;aborts=0;complete=1;last=0;status='completed';trace=zeros(N+1,30);
for k=0:N
    t=k*h;z=a+f.white(k+1)+f.colored(k+1);[x,P,innov,S]=pp_update(x,P,z,c);
    trace(k+1,1:20)=[t,a-c.mean_a0_m,m,x(1)-c.mean_a0_m,x(2),x(3),x(4),P(1,1),P(2,2)+2*P(2,3)+P(3,3),0,0,mode,timer,0,fuel*1000,energy/3600,f.bias+f.u(k+1),z,innov,S];
    trace(k+1,21:30)=[P(1,1),P(1,2),P(1,3),P(1,4),P(2,2),P(2,3),P(2,4),P(3,3),P(3,4),P(4,4)];
    if k==N,break;end
    if ~isempty(progress)&&mod(k,100)==0
        if ~progress(k/N),complete=0;status='cancelled';break;end
    end
    if any(~isfinite([x;P(:)]))||m<=0||a-c.earth_radius_m<c.model_altitude_min_m||a-c.earth_radius_m>c.model_altitude_max_m,complete=0;status='invalid_or_domain_exit';break;end
    if t>=main
        if finish-t<=c.terminal_horizon_s,[request,Twanted]=pp_terminal_plan(x,m,rho,t,finish,mode,timer,target,c);
        else
            gain=2*sqrt(x(1)^3/c.mu);dhat=pp_drag(x(1),m,x(2)+x(3),rho,c);
            err=target+gain*dhat*(1-c.available_fraction)*c.availability_period_s-x(1);request=err>c.terminal_deadband_m;
            Twanted=min(max(m*(dhat+max(err,0)/(gain*c.settlement_response_s)),c.throttle_min_fraction*c.thrust_max_N),c.thrust_max_N);
        end
    elseif ip==0
        if mod(k,round(c.periodic_interval_s/h))==0,credit=credit+pp_drag(c.mean_a0_m,c.mass_kg,0,rho,c)*c.mass_kg*c.periodic_interval_s*c.periodic_impulse_gain;end
        request=credit>0;Twanted=c.thrust_max_N;
    else
        signal=x(1);
        if ip==2,signal=signal-2*sqrt(x(1)^3/c.mu)*pp_drag(x(1),m,x(2)+x(3),rho,c)*c.predictive_horizon_s;end
        if signal<c.mean_a0_m+c.lower_trigger_m,latch=true;end
        if x(1)>c.mean_a0_m+c.upper_trigger_m,latch=false;end
        request=latch;Twanted=c.thrust_max_N;
    end
    [mode,timer,T,power,ab,fl]=pp_actuator(mode,timer,request,Twanted,t,finish,c);aborts=aborts+ab;powerfault=powerfault+fl;
    trace(k+1,10:14)=[T,power,mode,timer,double(request)];
    [a,m]=pp_plant(a,m,T,f.bias+f.u(k+1),f.bias+(f.u(k+1)+f.u(k+2))/2,f.bias+f.u(k+2),rho,h,c);
    fuel=fuel+T*h/(c.Isp_s*c.g0);energy=energy+power*h;timer=timer+h;last=k+1;
    if ip==0&&t<main,credit=credit-T*h;end
    vio=max(abs(a-c.mean_a0_m)-c.service_mean_a_halfband_m,0);maxvio=max(maxvio,vio);
    if vio>0,viotime=viotime+h;end
    if t<main,mainvio=max(mainvio,vio);end
    [x,P,~,~]=pp_predict(x,P,m+T*h/(c.Isp_s*c.g0),T,rho,c);
end
if last~=N||~isfinite(a)||~isfinite(m)||any(~isfinite(trace(1:last+1,:)),'all')||any(~isfinite(P(:)))||m<=0||a-c.earth_radius_m<c.model_altitude_min_m||a-c.earth_radius_m>c.model_altitude_max_m,complete=0;if strcmp(status,'completed'),status='invalid_or_domain_exit';end,end
error=a-target;masserr=abs((c.mass_kg-m)-fuel);service=complete==1&&maxvio==0;terminal=complete==1&&abs(error)<=c.terminal_tolerance_m;resource=powerfault==0&&aborts==0&&masserr<1e-8;
result=struct('completed',double(complete),'service_pass',double(service),'terminal_pass',double(terminal),'resource_pass',double(resource),'qualified',double(service&&terminal&&resource), ...
    'fuel_g',1000*(c.mass_kg-m),'energy_Wh',energy/3600,'terminal_error_m',error,'terminal_offset_m',a-c.mean_a0_m,'max_violation_m',maxvio,'violation_duration_s',viotime,'main_max_violation_m',mainvio,'power_faults',powerfault,'minimum_on_aborts',aborts,'mass_account_error_kg',masserr,'last_time_s',last*h, ...
    'rq',rq,'policy',policy,'rho0',rho,'terminal_target_offset_m',targetOffset,'schema',c.schema,'status',status);
trace=trace(1:last+1,:);
end
