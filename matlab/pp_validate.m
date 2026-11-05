function pp_validate(c)
fields=[{'available_fraction','throttle_min_fraction','initial_offset_m','lower_trigger_m','upper_trigger_m','model_altitude_min_m','model_altitude_max_m','terminal_root_iterations','terminal_numeric_tie_m'}];
for j=1:numel(fields),validateattributes(c.(fields{j}),{'numeric'},{'scalar','real','finite'});end
assert(c.terminal_numeric_tie_m>=0,'PP:Config','Negative numeric tie');
positive={'mu','g0','earth_radius_m','mass_kg','Isp_s','thrust_max_N','nominal_propulsion_power_W','mean_a0_m','service_mean_a_halfband_m','terminal_tolerance_m','step_s','Cd','area_m2','scale_height_m','availability_period_s','ou_tau_s','measurement_sigma_m','colored_tau_s','settlement_response_s','terminal_horizon_s','observer_prior_a_variance_m2','periodic_interval_s'};
for j=1:numel(positive),validateattributes(c.(positive{j}),{'numeric'},{'scalar','real','finite','positive'});end
nonnegative={'main_duration_days','common_settlement_days','warmup_s','minimum_on_s','minimum_off_s','passive_cooldown_s','bias_sigma','ou_sigma','colored_sigma_m','predictive_horizon_s','terminal_deadband_m','periodic_impulse_gain','propulsion_allocation_W'};
for j=1:numel(nonnegative),validateattributes(c.(nonnegative{j}),{'numeric'},{'scalar','real','finite','nonnegative'});end
assert(c.available_fraction>0&&c.available_fraction<=1&&c.throttle_min_fraction>0&&c.throttle_min_fraction<=1,'PP:Config','Fraction');
assert(c.initial_offset_m==0&&c.lower_trigger_m<c.upper_trigger_m,'PP:Config','Start/triggers');
assert(c.mean_a0_m-c.earth_radius_m>c.model_altitude_min_m&&c.mean_a0_m-c.earth_radius_m<c.model_altitude_max_m,'PP:Config','Initial domain');
v=[(c.main_duration_days+c.common_settlement_days)*86400,c.main_duration_days*86400,c.availability_period_s,c.available_fraction*c.availability_period_s,c.warmup_s,c.minimum_on_s,c.minimum_off_s,c.passive_cooldown_s,c.periodic_interval_s,c.terminal_horizon_s];
assert(all(abs(v/c.step_s-round(v/c.step_s))<=1e-8)&&v(1)>=c.step_s,'PP:Config','Grid alignment');
assert(c.terminal_root_iterations==round(c.terminal_root_iterations)&&c.terminal_root_iterations>=1&&c.terminal_root_iterations<=40,'PP:Config','Root iterations');
end
