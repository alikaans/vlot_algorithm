function pp_app(rq)
%PP_APP R2021a+. Shared saved input is the default; native RNG is exploratory.
pp_require_validation();root=fileparts(fileparts(mfilename('fullpath')));
w=uifigure('Name',['PP-1.0 | ' rq],'Position',[60 60 1180 780]);
g=uigridlayout(w,[4 1]);g.RowHeight={55,50,'1x',150};
head=uigridlayout(g,[1 4]);uilabel(head,'Text',[rq ' | hedef ' num2str(pp_mission_target(rq)) ' m']);
source=uidropdown(head,'Items',{'Ortak kayitli 37 gun','Ortak kayitli kisa kontrol','MATLAB yerel RNG (kesif)'});
seed=uieditfield(head,'numeric','Value',72001,'Limits',[72001 72030],'RoundFractionalValues','on');
run=uibutton(head,'Text','Uc yontemi calistir','ButtonPushedFcn',@execute);
options=uigridlayout(g,[1 6]);uilabel(options,'Text','rho0 [kg/m^3]');rho=uidropdown(options,'Items',{'5e-12','1e-11','2e-11','4e-11','8e-11'},'Value','2e-11');
uilabel(options,'Text','Kutle [kg]');mass=uieditfield(options,'numeric','Value',35.6,'Limits',[1 Inf]);uilabel(options,'Text','Guc erisim orani');fraction=uieditfield(options,'numeric','Value',.6,'Limits',[.01 1]);
tabs=uitabgroup(g);ax1=uiaxes(uitab(tabs,'Title','Yorunge'));ax1.Position=[40 30 1050 430];
ax2=uiaxes(uitab(tabs,'Title','Yakit'));ax2.Position=ax1.Position;ax3=uiaxes(uitab(tabs,'Title','Enerji'));ax3.Position=ax1.Position;
ax4=uiaxes(uitab(tabs,'Title','Itki'));ax4.Position=ax1.Position;ax5=uiaxes(uitab(tabs,'Title','Atmosfer'));ax5.Position=ax1.Position;
ax6=uiaxes(uitab(tabs,'Title','Kestirim hatasi'));ax6.Position=ax1.Position;
info=uitextarea(g,'Editable','off','Value',{'Once tam MATLAB dogrulamasi gerekir. Kayitli modda sure, rho, kutle ve guc girdiden alinir.','Yerel RNG modu: ayni seed Python ile ayni atmosfer demek degildir.','Tum sonuclar gelistirme amaclidir; yakit ustunlugu sonucu otomatik uretilmez.'});
    function execute(~,~)
        run.Enable='off';cleanup=onCleanup(@unlock);dlg=[];
        try
            pp_require_validation();
            if startsWith(source.Value,'Ortak')
                kind='full';if contains(source.Value,'kisa'),kind='quick';end
                d=load(fullfile(root,'fixtures',['shared_' kind '.mat']));c=pp_numeric_spec(d.c);rr=double(d.rho);
                f=struct('bias',d.bias,'u',d.u(:),'white',d.white(:),'colored',d.colored(:));inputSeed=d.seed;provenance=['saved shared_' kind];
            else
                c=pp_load_spec();c.mass_kg=mass.Value;c.available_fraction=fraction.Value;rr=str2double(rho.Value);pp_validate(c);inputSeed=seed.Value;f=pp_make_forcing(c,inputSeed);provenance='MATLAB native twister; not Python seed parity';
            end
            axesList={ax1,ax2,ax3,ax4,ax5,ax6};for ai=1:numel(axesList),cla(axesList{ai});hold(axesList{ai},'on');end
            [~,uniquePart]=fileparts(tempname);stamp=[datestr(now,'yyyymmdd_HHMMSS') '_' uniquePart];folder=fullfile(root,'results',rq,stamp);mkdir(folder);
            meta=struct('rq',rq,'target_offset_m',pp_mission_target(rq),'rho0',rr,'seed',inputSeed,'provenance',provenance,'spec',c,'runtime',version,'manifest_sha256',pp_sha256(fullfile(root,'MANIFEST_SHA256.json')));
            pp_write_json(fullfile(folder,'metadata.json'),meta);save(fullfile(folder,'shared_input.mat'),'c','f','rr','inputSeed');
            policies={'periodic','hysteresis','predictive_hysteresis'};records=cell(1,3);
            dlg=uiprogressdlg(w,'Title','PP deney','Cancelable','on');
            for i=1:3
                [result,trace]=pp_simulate(c,rq,policies{i},rr,f,@progress);records{i}=result;save(fullfile(folder,[policies{i} '.mat']),'result','trace');
                writematrix(trace,fullfile(folder,[policies{i} '_trace.csv']));x=trace(:,1)/86400;
                plot(ax1,x,trace(:,2),'DisplayName',policies{i});plot(ax2,x,trace(:,15),'DisplayName',policies{i});plot(ax3,x,trace(:,16),'DisplayName',policies{i});stairs(ax4,x,trace(:,10)*1e6,'DisplayName',policies{i});
                plot(ax5,x,exp(trace(:,17)),'DisplayName',policies{i});plot(ax6,x,trace(:,2)-trace(:,4),'DisplayName',policies{i});
                if strcmp(result.status,'cancelled'),records=records(1:i);break;end
            end
            yline(ax1,pp_mission_target(rq),'--','hedef');yline(ax1,c.service_mean_a_halfband_m,':');yline(ax1,-c.service_mean_a_halfband_m,':');
            titles={'Ortalama yari buyuk eksen farki [m]','Toplam yakit [g]','Toplam enerji [Wh]','Uygulanan itki [microN]','exp(b+u) carpan','Gercek - kestirilen a [m]'};
            for ai=1:numel(axesList),title(axesList{ai},titles{ai});xlabel(axesList{ai},'Gun');legend(axesList{ai},'Location','best','Interpreter','none');grid(axesList{ai},'on');end
            results=[records{:}];writetable(struct2table(results),fullfile(folder,'summary.csv'));pp_write_json(fullfile(folder,'summary.json'),results);
            lines={['Kayit: ' folder],['Girdi: ' provenance ' | rho=' num2str(rr) ' | kutle=' num2str(c.mass_kg) ' | erisim=' num2str(c.available_fraction)]};
            for i=1:numel(records),z=records{i};lines{end+1}=sprintf('%s | completed=%d qualified=%d | hata=%.3f m | yakit=%.4f g',z.policy,z.completed,z.qualified,z.terminal_error_m,z.fuel_g);end
            info.Value=lines;
        catch err
            if ~isempty(dlg)&&isvalid(dlg),close(dlg);end
            uialert(w,err.message,'PP hata');return
        end
        if ~isempty(dlg)&&isvalid(dlg),close(dlg);end
        function keep=progress(v)
            dlg.Value=((i-1)+v)/3;dlg.Message=policies{i};drawnow;keep=~dlg.CancelRequested;
        end
    end
    function unlock(),if isvalid(run),run.Enable='on';end,end
end
