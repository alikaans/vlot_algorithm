function c=pp_numeric_spec(c)
%PP_NUMERIC_SPEC Normalize numerical model parameters at the input boundary.
% scipy.io.savemat preserves Python integers as int64. MATLAB mixed integer /
% double arithmetic and concatenation can round whole trace rows to integers.
% Counts remain integer-valued but use double storage for model calculations.
assert(isstruct(c)&&isscalar(c),'PP:Config','Scalar config struct required');
names=fieldnames(c);
for k=1:numel(names)
    name=names{k};
    if isnumeric(c.(name)),c.(name)=double(c.(name));end
end
end
