function d=pp_drag(a,m,eta,rho,c)
d=.5*rho*exp(-(a-c.mean_a0_m)/c.scale_height_m+eta)*c.Cd*c.area_m2*c.mu/a/m;
end
