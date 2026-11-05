function pp_write_json(path,value)
fid=fopen(path,'w','n','UTF-8');assert(fid>=0,'PP:IO','Cannot write result');cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s',jsonencode(value));
end
