
drop table agent;
update cloudsponge_raw set geolocation ='Greater New York City Area';
create table agent as
select cloudsponge_raw.user_email as email, cloudsponge_raw.geolocation 
from cloudsponge_raw
group by cloudsponge_raw.user_email, cloudsponge_raw.geolocation;
select * from agent;
ALTER TABLE agent ADD PRIMARY KEY (email);
ALTER TABLE cloudsponge_raw ADD  FOREIGN KEY(user_email) REFERENCES agent(email);
alter table agent add column public_url citext;
alter table agent add column first_name citext;
alter table agent add column email_contacts_from_email json;
alter table agent add column email_contacts_from_linkedin json;