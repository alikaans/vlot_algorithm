function hex=pp_sha256(path)
%PP_SHA256 Native OS SHA-256; no JVM and no Python dependency.
% Windows: PowerShell Get-FileHash. Linux: sha256sum. macOS: shasum.
% The path is passed as environment DATA, never interpolated into shell code.
validateattributes(path,{'char','string'},{'nonempty'});path=char(path);
assert(isrow(path)&&~any(path==char(0)),'PP:Hash','Invalid file path');
[ok,attr]=fileattrib(path);assert(ok&&~attr.directory,'PP:Hash','Cannot open file: %s',path);
old=getenv('PP_SHA256_INPUT');cleanup=onCleanup(@() setenv('PP_SHA256_INPUT',old)); %#ok<NASGU>
setenv('PP_SHA256_INPUT',attr.Name);
if ispc
    cmd='powershell.exe -NoLogo -NoProfile -NonInteractive -Command "(Get-FileHash -LiteralPath $env:PP_SHA256_INPUT -Algorithm SHA256 -ErrorAction Stop).Hash"';
elseif ismac
    cmd='shasum -a 256 < "$PP_SHA256_INPUT"';
else
    cmd='sha256sum < "$PP_SHA256_INPUT"';
end
[status,out]=system(cmd);
assert(status==0,'PP:HashUnavailable','Native SHA-256 command failed. Windows requires PowerShell Get-FileHash; Linux sha256sum; macOS shasum. Detail: %s',strtrim(out));
token=regexp(strtrim(out),'^([0-9a-fA-F]{64})(?:\s|$)','tokens','once');
assert(~isempty(token),'PP:HashOutput','Native SHA-256 returned an invalid digest: %s',strtrim(out));
hex=lower(token{1});
end
