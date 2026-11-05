function report=verify_pp(suite)
%VERIFY_PP Fixed inputs/thresholds; never generates expected results.
if nargin<1,suite='full';end
assert(any(strcmp(suite,{'quick','full'})),'PP:Suite','quick or full');
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'));
report=struct('schema','PP-1.0','passed',false,'suite',suite,'runtime',version,'checked_at',datestr(now,30),'checks',struct([]),'manifest_sha256','');
try
    report.hash_selftest=pp_hash_selftest();
    manifest=jsondecode(fileread(fullfile(root,'MANIFEST_SHA256.json')));
    for i=1:numel(manifest.files)
        e=manifest.files(i);actual=pp_sha256(fullfile(root,strrep(e.path,'/',filesep)));
        assert(strcmp(actual,e.sha256),'PP:SourceChanged','Package source/fixture changed: %s',e.path);
    end
    report.manifest_sha256=pp_sha256(fullfile(root,'MANIFEST_SHA256.json'));
    report.numeric_type_selftest=pp_type_selftest();
    tol=jsondecode(fileread(fullfile(root,'config','tolerances.json')));
    v=load(fullfile(root,'fixtures','components.mat'));c=pp_numeric_spec(v.c);
    for i=1:size(v.edges_input,1)
        a=v.edges_input(i,:);[md,tm,T,P,ab,fl]=pp_actuator(a(1),a(2),logical(a(3)),a(4),a(5),a(6),c);
        assert(all(abs([md,tm,T,P,ab,fl]-v.edges_expected(i,:))<=tol.actuator_absolute(:)'),'PP:Actuator','Edge %d failed',i);
    end
    for i=1:numel(v.math_probes)
        z=v.math_probes{i};cc=c;cc.step_s=z.h;
        [xp,pp,F,Q]=pp_predict(z.x(:),z.P,z.m,z.T,z.rho,cc);
        [xn,pn,innov,S]=pp_update(xp,pp,z.z,cc);
        differences=[max(abs(xp-z.xp(:))),max(abs(pp-z.pp),[],'all'),max(abs(F-z.F),[],'all'),max(abs(Q-z.Q),[],'all'),max(abs(xn-z.xn(:))),max(abs(pn-z.pn),[],'all'),abs(innov-z.innov),abs(S-z.S)];
        assert(all(differences<=tol.observer_math_absolute),'PP:Observer','Probe %d failed',i);
    end
    kinds={'quick'};if strcmp(suite,'full'),kinds={'quick','full'};end
    for ki=1:numel(kinds)
        d=load(fullfile(root,'fixtures',['shared_' kinds{ki} '.mat']));c=pp_numeric_spec(d.c);
        f=struct('bias',d.bias,'u',d.u(:),'white',d.white(:),'colored',d.colored(:));
        for j=1:6
            name=strtrim(d.case_names{j});parts=strsplit(name,'/');
            fprintf('PP parity: %s / %s ...\n',kinds{ki},name);
            [r,tr]=pp_simulate(c,parts{1},parts{2},d.rho,f);
            metric=zeros(1,numel(d.metric_names));for k=1:numel(d.metric_names),metric(k)=r.(strtrim(d.metric_names{k}));end
            me=abs(metric-d.expected_metrics(j,:));expected=d.expected_trace{j};sample=tr(d.sample_indices,:);
            td=abs(sample-expected);te=max(td,[],1);ce=max(abs(tr(:,10:14)-d.expected_commands{j}),[],1);
            ok=all(me<=tol.metrics_absolute(:)')&&all(te<=tol.trace_absolute(:)')&&all(ce<=tol.commands_absolute(:)');
            first=struct([]);bad=~isfinite(td)|td>tol.trace_absolute(:)';row=find(any(bad,2),1);
            if ~isempty(row)
                col=find(bad(row,:),1);first=struct('time_s',sample(row,1),'column',col,'name',strtrim(d.trace_names{col}),'actual',sample(row,col),'expected',expected(row,col),'absolute_error',td(row,col),'tolerance',tol.trace_absolute(col));
            end
            item=struct('kind',kinds{ki},'case_name',name,'passed',ok,'metric_error',me,'trace_max_error',te,'command_max_error',ce,'first_trace_mismatch',first,'source_main_duration_class',class(d.c.main_duration_days),'normalized_main_duration_class',class(c.main_duration_days));
            if isempty(report.checks),report.checks=item;else,report.checks(end+1)=item;end %#ok<AGROW>
            assert(ok,'PP:Parity','First failed parity case: %s / %s. Keep expected values and tolerances unchanged.',kinds{ki},name);
        end
    end
    report.passed=true;report.component_edges=size(v.edges_input,1);report.component_observer_probes=numel(v.math_probes);
catch err
    report.error_identifier=err.identifier;report.error_message=err.message;
    pp_write_json(fullfile(root,'validation','matlab_validation.json'),report);
    rethrow(err);
end
pp_write_json(fullfile(root,'validation','matlab_validation.json'),report);
fprintf('PASS PP %s parity. This is implementation agreement, not flight validation.\n',suite);
end
