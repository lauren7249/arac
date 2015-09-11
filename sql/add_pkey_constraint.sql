alter table bing_searches drop constraint pkey;
alter table bing_searches add column inbody citext;
update bing_searches set inbody='';
alter table bing_searches add constraint pkey primary key (terms, site, intitle, inbody);