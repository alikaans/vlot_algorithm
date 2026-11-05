function [a,m]=pp_plant(a,m,T,e0,em,e1,rho,h,c)
dm=-T/(c.Isp_s*c.g0);
k1=rhs(a,m,e0,T,rho,c);k2=rhs(a+h*k1/2,m+h*dm/2,em,T,rho,c);
k3=rhs(a+h*k2/2,m+h*dm/2,em,T,rho,c);k4=rhs(a+h*k3,m+h*dm,e1,T,rho,c);
a=a+h*(k1+2*k2+2*k3+k4)/6;m=m+h*dm;
end
function q=rhs(a,m,eta,T,rho,c)
q=2*sqrt(a^3/c.mu)*(T/m-pp_drag(a,m,eta,rho,c));
end
