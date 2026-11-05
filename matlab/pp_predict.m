function [xp,pp,F,Q]=pp_predict(x,P,m,T,rho,c)
h=c.step_s;a=x(1);gain=2*sqrt(a^3/c.mu);d=pp_drag(a,m,x(2)+x(3),rho,c);
alpha=1.5*gain/a*(T/m-d)-gain*d*(-1/c.scale_height_m-1/a);g=-gain*d;
F=pp_phi(alpha,g,h,c);Q=zeros(4);qu=2*c.ou_sigma^2/c.ou_tau_s;
GN=[-.906179845938664,-.538469310105683,0,.538469310105683,.906179845938664];
GW=[.236926885056189,.478628670499366,.568888888888889,.478628670499366,.236926885056189];
for k=1:5,M=pp_phi(alpha,g,h*(GN(k)+1)/2,c);v=M(:,3);Q=Q+h*GW(k)/2*qu*(v*v');end
Q(4,4)=c.colored_sigma_m^2*(-expm1(-2*h/c.colored_tau_s));
uh=x(3)*exp(-h/(2*c.ou_tau_s));ue=x(3)*exp(-h/c.ou_tau_s);
[aa,~]=pp_plant(a,m,T,x(2)+x(3),x(2)+uh,x(2)+ue,rho,h,c);
xp=[aa;x(2);ue;x(4)*exp(-h/c.colored_tau_s)];pp=F*P*F'+Q;pp=(pp+pp')/2;
end
