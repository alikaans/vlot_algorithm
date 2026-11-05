function target=pp_mission_target(rq)
assert(any(strcmp(rq,{'RQ1','RQ2'})),'PP:RQ','RQ1 or RQ2 required');
root=fileparts(fileparts(mfilename('fullpath')));missions=jsondecode(fileread(fullfile(root,'config','missions.json')));
target=missions.(rq).target_offset_m;
end
