function report=pp_hash_selftest()
%PP_HASH_SELFTEST Fixed independent SHA-256 vectors, including binary bytes.
folder=[tempname '_PP space [x]'];[ok,msg]=mkdir(folder);assert(ok,'PP:HashTest','%s',msg);
cleanup=onCleanup(@() rmdir(folder,'s')); %#ok<NASGU>
inputs={uint8([]),uint8('abc'),uint8(0:255)};
expected={'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', ...
    'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad', ...
    '40aff2e9d2d8922e47afd4648e6967497158785fbd1da870e7110266bf944880'};
for k=1:numel(inputs)
    path=fullfile(folder,sprintf('vector_%d.bin',k));write_bytes(path,inputs{k});
    actual=pp_sha256(path);assert(strcmp(actual,expected{k}),'PP:HashTest','SHA-256 vector %d failed',k);
end
report=struct('passed',true,'fixed_vectors',numel(inputs),'java_required',false,'path_test','spaces and square brackets');
end
function write_bytes(path,bytes)
fid=fopen(path,'wb');assert(fid>=0,'PP:HashTest','Cannot write test input');cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
count=fwrite(fid,bytes,'uint8');assert(count==numel(bytes),'PP:HashTest','Short write');
end
