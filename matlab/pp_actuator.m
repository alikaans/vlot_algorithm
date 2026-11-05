function [mode,timer,T,P,abort,fault]=pp_actuator(mode,timer,request,Twanted,t,finish,c)
remaining=c.available_fraction*c.availability_period_s-mod(t,c.availability_period_s);
cap=0;if remaining>0,cap=c.propulsion_allocation_W;end
abort=0;
if mode==0&&request&&timer>=c.minimum_off_s&&remaining>=c.warmup_s+c.minimum_on_s&&finish-t>=c.warmup_s+c.minimum_on_s&&cap>=c.nominal_propulsion_power_W
    mode=1;timer=0;
elseif mode==1&&timer>=c.warmup_s,mode=2;timer=0;
elseif mode==2&&((~request&&timer>=c.minimum_on_s)||cap<c.nominal_propulsion_power_W)
    if timer<c.minimum_on_s,abort=1;end
    mode=3;timer=0;
elseif mode==3&&timer>=c.passive_cooldown_s,mode=0;timer=0;
end
T=0;P=0;
if mode==1,P=c.nominal_propulsion_power_W;end
if mode==2,T=min(max(Twanted,c.throttle_min_fraction*c.thrust_max_N),c.thrust_max_N);P=c.nominal_propulsion_power_W*T/c.thrust_max_N;end
fault=0;
if P>cap+1e-12,T=0;P=0;mode=3;timer=0;fault=1;end
end
