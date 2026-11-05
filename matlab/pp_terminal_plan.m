function [bestR,bestT]=pp_terminal_plan(x,m,rho,t,finish,mode,timer,target,c)
[~,first,~]=schedule(t,finish,mode,timer,finish,c);minstop=t;
if first>=0
    if mode==2&&first==0,needed=max(c.minimum_on_s-timer,c.step_s);else,needed=c.minimum_on_s;end
    minstop=t+first*c.step_s+needed;
end
stops=[finish,minstop,t];bestV=1e99;bestE=1e99;bestLast=-1;bestT=c.throttle_min_fraction*c.thrust_max_N;bestR=false;
for k=1:3
    [on,~,last]=schedule(t,finish,mode,timer,stops(k),c);[T,af,v]=fit(x,m,on,rho,target,c);err=abs(af-target);better=v<bestV;
    if v==bestV
        if err<=c.terminal_numeric_tie_m&&bestE<=c.terminal_numeric_tie_m,better=last>bestLast;
        elseif err<=c.terminal_numeric_tie_m,better=true;
        elseif bestE<=c.terminal_numeric_tie_m,better=false;
        else,better=err<bestE;end
    end
    if better,bestV=v;bestE=err;bestLast=last;bestT=T;bestR=t<stops(k);end
end
end
function [on,first,last]=schedule(t,finish,mode,timer,stop,c)
count=round((finish-t)/c.step_s);on=false(count,1);first=-1;last=-1;
for k=0:count-1
    tt=t+k*c.step_s;[mode,timer,T,~,~,~]=pp_actuator(mode,timer,tt<stop,c.thrust_max_N,tt,finish,c);
    if T>0,on(k+1)=true;last=k;if first<0,first=k;end,end
    timer=timer+c.step_s;
end
end
function [T,af,v]=fit(x,m,on,rho,target,c)
low=c.throttle_min_fraction*c.thrust_max_N;high=c.thrust_max_N;
[al,vl]=forecast(x,m,low,on,rho,c);[ah,vh]=forecast(x,m,high,on,rho,c);
if al>=target,T=low;af=al;v=vl;return;end
if ah<=target,T=high;af=ah;v=vh;return;end
for k=1:c.terminal_root_iterations
    mid=(low+high)/2;[am,~]=forecast(x,m,mid,on,rho,c);
    if am<target,low=mid;else,high=mid;end
end
T=(low+high)/2;[af,v]=forecast(x,m,T,on,rho,c);
end
function [a,peak]=forecast(x,m,T,on,rho,c)
a=x(1);u=x(3);peak=max(abs(a-c.mean_a0_m)-c.service_mean_a_halfband_m,0);h=c.step_s;
for k=1:numel(on)
    force=0;if on(k),force=T;end
    um=u*exp(-h/(2*c.ou_tau_s));ue=u*exp(-h/c.ou_tau_s);
    [a,m]=pp_plant(a,m,force,x(2)+u,x(2)+um,x(2)+ue,rho,h,c);u=ue;
    peak=max(peak,abs(a-c.mean_a0_m)-c.service_mean_a_halfband_m);
end
end
