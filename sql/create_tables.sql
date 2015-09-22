/**criteria for using a proxy:
	not used for a particular domain in the last 15-45 seconds 
	not rejected by the domain in the last 24 hours
	not timed out in the last 48 hours and less than 3 consecutive time outs, or successful more recently than timeout
	most recently successful

table:
	proxy
	domain
	last_rejected
	last_used
	last_timeout
**/
CREATE unlogged TABLE proxy_domain_status (
    proxy_url           varchar(30) NOT NULL references proxy(url),
    domain         	varchar(100) NOT NULL,   
    PRIMARY KEY (proxy_url, domain),   
    last_rejected    timestamp,           
    last_accepted	 timestamp    
);

CREATE UNLOGGED TABLE proxy_domain_event (
	id serial PRIMARY KEY,
    proxy_url           varchar(30) NOT NULL,
    domain         	varchar(100) NOT NULL,   
    event_time    timestamp NOT NULL,           
    status_code	 varchar(3),
    success BOOLEAN NOT NULL
);

create table phone_exports (
    id varchar(200) primary key not null,
    sent_from  citext,
    data  text
);


create table cloudsponge_raw (
	id serial primary key not null,
    user_email CITEXT,
	contacts_owner json,
	contact json
);
CREATE TABLE proxy (
    url           varchar(30) PRIMARY KEY NOT NULL,       
    last_timeout   timestamp,       
    last_success    timestamp,    
    consecutive_timeouts       int         
);

CREATE TABLE prospect_urls (
    url           varchar(200) PRIMARY KEY NOT NULL,       
    linkedin_id  
);

CREATE TABLE facebook (
    facebook_id           varchar(200) PRIMARY KEY NOT NULL,  
    linkedin_id bigint,     
    prospect_id   int,
    info   json
);

CREATE TABLE pipl_from_facebook (
    facebook_id           varchar(200) PRIMARY KEY NOT NULL,       
    linkedin_url   varchar(150),
    pipl_response   json
);


CREATE TABLE pipl_from_email (
    email           varchar(200) PRIMARY KEY NOT NULL,       
    linkedin_url   varchar(150),
    pipl_response   json
);

CREATE TABLE facebook_urls (     
    url   CITEXT PRIMARY KEY NOT NULL,
    username    CITEXT NOT NULL references facebook_contacts(facebook_id)
);

CREATE TABLE linkedin_schools (
    id          int PRIMARY KEY NOT NULL,       
    pretty_url varchar(150) ,
    name varchar(100),
    image_url varchar(300)
);

CREATE TABLE bing_searches (
    terms CITEXT NOT NULL,  
    site CITEXT NOT NULL,
    intitle CITEXT NOT NULL,
    PRIMARY KEY (terms, site, intitle),
    pages int,
    next_querystring varchar(300),
    results json
);

CREATE TABLE geocoded_locations (
    raw_location CITEXT NOT NULL,

);

CREATE TABLE google_profile_searches (
    terms           varchar(300) NOT NULL,
    name          varchar(200),   
    PRIMARY KEY (terms, name),   
    url    varchar(200)
);

alter table education add column school_linkedin_id int references linkedin_schools(id);

create table mapquest_geocode (
    name CITEXT primary key not null,
    geocode json
);

update proxy_domain_status s set last_used = now() from (select id from proxy_domain_status where last_used BETWEEN now()::timestamp - (interval '1s') * 1000 AND now()::timestamp - (interval '1s') * 60 limit 1 FOR UPDATE) sub where s.id=sub.id returning *;

#"//script[contains(.,'background_view')]" - e