function [xn,pn,innov,S]=pp_update(x,P,z,c)
R=c.measurement_sigma_m^2;ph=P(:,1)+P(:,4);S=P(1,1)+2*P(1,4)+P(4,4)+R;
assert(isfinite(S)&&S>0,'PP:Numerical','Nonpositive innovation covariance');
K=ph/S;innov=z-x(1)-x(4);xn=x+K*innov;M=eye(4);M(:,1)=M(:,1)-K;M(:,4)=M(:,4)-K;
pn=M*P*M'+R*(K*K');pn=(pn+pn')/2;
end
