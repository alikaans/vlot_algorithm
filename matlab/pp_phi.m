function F=pp_phi(alpha,g,h,c)
F=zeros(4);eu=exp(-h/c.ou_tau_s);F(1,1)=exp(alpha*h);F(1,2)=g*divided(alpha,h);
F(1,3)=g*eu*divided(alpha+1/c.ou_tau_s,h);F(2,2)=1;F(3,3)=eu;F(4,4)=exp(-h/c.colored_tau_s);
end
function v=divided(a,h)
if abs(a*h)<1e-8,v=h*(1+a*h/2+(a*h)^2/6+(a*h)^3/24);else,v=expm1(a*h)/a;end
end
