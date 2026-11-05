function c=pp_load_spec(path)
%PP_LOAD_SPEC The single numeric contract is config/spec.json.
if nargin<1,root=fileparts(fileparts(mfilename('fullpath')));path=fullfile(root,'config','spec.json');end
c=pp_numeric_spec(jsondecode(fileread(path)));pp_validate(c);
end
