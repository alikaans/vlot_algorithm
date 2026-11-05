function pp_require_validation()
root=fileparts(fileparts(mfilename('fullpath')));path=fullfile(root,'validation','matlab_validation.json');
assert(exist(path,'file')==2,'PP:ValidationRequired','First run verify_pp(''full'').');
r=jsondecode(fileread(path));assert(r.passed&&strcmp(r.suite,'full'),'PP:ValidationRequired','Full MATLAB parity has not passed. Run verify_pp(''full'').');
assert(strcmp(r.manifest_sha256,pp_sha256(fullfile(root,'MANIFEST_SHA256.json'))),'PP:SourceChanged','Package changed since validation. Revalidate.');
m=jsondecode(fileread(fullfile(root,'MANIFEST_SHA256.json')));
for i=1:numel(m.files),e=m.files(i);assert(strcmp(pp_sha256(fullfile(root,strrep(e.path,'/',filesep))),e.sha256),'PP:SourceChanged','Changed package: %s',e.path);end
end
