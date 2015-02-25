--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: company; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE company (
    id integer NOT NULL,
    name character varying(1024)
);


ALTER TABLE public.company OWNER TO arachnid;

--
-- Name: company_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE company_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.company_id_seq OWNER TO arachnid;

--
-- Name: company_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE company_id_seq OWNED BY company.id;


--
-- Name: education_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE education_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.education_id_seq OWNER TO arachnid;

--
-- Name: education; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE education (
    id integer DEFAULT nextval('education_id_seq'::regclass) NOT NULL,
    school_id integer,
    prospect_id integer,
    degree character varying(200),
    start_date date,
    end_date date
);


ALTER TABLE public.education OWNER TO arachnid;

--
-- Name: industry; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE industry (
    id integer NOT NULL,
    name character varying(1024)
);


ALTER TABLE public.industry OWNER TO arachnid;

--
-- Name: industry_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE industry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.industry_id_seq OWNER TO arachnid;

--
-- Name: industry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE industry_id_seq OWNED BY industry.id;


--
-- Name: job_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE job_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.job_id_seq OWNER TO arachnid;

--
-- Name: job; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE job (
    id integer DEFAULT nextval('job_id_seq'::regclass) NOT NULL,
    company_id integer,
    prospect_id integer,
    title character varying(1024),
    start_date date,
    end_date date,
    location character varying(1024)
);


ALTER TABLE public.job OWNER TO arachnid;

--
-- Name: location; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE location (
    id integer NOT NULL,
    name character varying(1024)
);


ALTER TABLE public.location OWNER TO arachnid;

--
-- Name: location_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE location_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.location_id_seq OWNER TO arachnid;

--
-- Name: location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE location_id_seq OWNED BY location.id;


--
-- Name: prospect; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE prospect (
    id integer NOT NULL,
    url character varying(1024),
    name character varying(1024),
    linkedin_id character varying(1024),
    location integer,
    location_raw character varying,
    industry integer,
    industry_raw character varying(1024),
    s3_key character varying(1024),
    complete boolean,
    updated date,
    connections integer,
    image_url character varying(1024)
);


ALTER TABLE public.prospect OWNER TO arachnid;

--
-- Name: prospect_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE prospect_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.prospect_id_seq OWNER TO arachnid;

--
-- Name: prospect_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE prospect_id_seq OWNED BY prospect.id;


--
-- Name: prospect_school; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE prospect_school (
    id integer NOT NULL,
    name character varying,
    school integer,
    school_raw character varying(1024),
    "user" integer,
    start_date date,
    end_date date,
    degree character varying(200),
    body_tsv tsvector
);


ALTER TABLE public.prospect_school OWNER TO arachnid;

--
-- Name: prospect_school_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE prospect_school_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.prospect_school_id_seq OWNER TO arachnid;

--
-- Name: prospect_school_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE prospect_school_id_seq OWNED BY prospect_school.id;


--
-- Name: s3work; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE s3work (
    id integer NOT NULL,
    s3_key character varying(1024),
    complete boolean
);


ALTER TABLE public.s3work OWNER TO arachnid;

--
-- Name: s3work_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE s3work_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.s3work_id_seq OWNER TO arachnid;

--
-- Name: s3work_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE s3work_id_seq OWNED BY s3work.id;


--
-- Name: school; Type: TABLE; Schema: public; Owner: arachnid; Tablespace:
--

CREATE TABLE school (
    id integer NOT NULL,
    name character varying(1024)
);


ALTER TABLE public.school OWNER TO arachnid;

--
-- Name: school_id_seq; Type: SEQUENCE; Schema: public; Owner: arachnid
--

CREATE SEQUENCE school_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.school_id_seq OWNER TO arachnid;

--
-- Name: school_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: arachnid
--

ALTER SEQUENCE school_id_seq OWNED BY school.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY company ALTER COLUMN id SET DEFAULT nextval('company_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY industry ALTER COLUMN id SET DEFAULT nextval('industry_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY location ALTER COLUMN id SET DEFAULT nextval('location_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY prospect ALTER COLUMN id SET DEFAULT nextval('prospect_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY prospect_school ALTER COLUMN id SET DEFAULT nextval('prospect_school_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY s3work ALTER COLUMN id SET DEFAULT nextval('s3work_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY school ALTER COLUMN id SET DEFAULT nextval('school_id_seq'::regclass);


--
-- Name: company_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY company
    ADD CONSTRAINT company_pkey PRIMARY KEY (id);


--
-- Name: industry_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY industry
    ADD CONSTRAINT industry_pkey PRIMARY KEY (id);


--
-- Name: location_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY location
    ADD CONSTRAINT location_pkey PRIMARY KEY (id);


--
-- Name: pk_education; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY education
    ADD CONSTRAINT pk_education PRIMARY KEY (id);


--
-- Name: pk_job; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY job
    ADD CONSTRAINT pk_job PRIMARY KEY (id);


--
-- Name: prospect_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY prospect
    ADD CONSTRAINT prospect_pkey PRIMARY KEY (id);


--
-- Name: prospect_school_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY prospect_school
    ADD CONSTRAINT prospect_school_pkey PRIMARY KEY (id);


--
-- Name: s3work_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY s3work
    ADD CONSTRAINT s3work_pkey PRIMARY KEY (id);


--
-- Name: school_pkey; Type: CONSTRAINT; Schema: public; Owner: arachnid; Tablespace:
--

ALTER TABLE ONLY school
    ADD CONSTRAINT school_pkey PRIMARY KEY (id);


--
-- Name: education_prospect_id_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX education_prospect_id_idx ON education USING btree (prospect_id);


--
-- Name: education_school_id_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX education_school_id_idx ON education USING btree (school_id);


--
-- Name: job_company_id_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX job_company_id_idx ON job USING btree (company_id);


--
-- Name: job_prospect_id_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX job_prospect_id_idx ON job USING btree (prospect_id);


--
-- Name: linkedin_id_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX linkedin_id_idx ON prospect USING btree (linkedin_id);


--
-- Name: prospect_school_id_fk; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX prospect_school_id_fk ON prospect_school USING btree ("user");


--
-- Name: prospect_school_tsv; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX prospect_school_tsv ON prospect_school USING gin (body_tsv);


--
-- Name: s3_key_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX s3_key_idx ON prospect USING btree (s3_key);


--
-- Name: school_raw_idx; Type: INDEX; Schema: public; Owner: arachnid; Tablespace:
--

CREATE INDEX school_raw_idx ON prospect_school USING btree (school_raw);


--
-- Name: tsvectorupdate; Type: TRIGGER; Schema: public; Owner: arachnid
--

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON prospect_school FOR EACH ROW EXECUTE PROCEDURE tsvector_update_trigger('body_tsv', 'pg_catalog.english', 'school_raw');


--
-- Name: education_prospect_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY education
    ADD CONSTRAINT education_prospect_fkey FOREIGN KEY (prospect_id) REFERENCES prospect(id);


--
-- Name: education_school_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY education
    ADD CONSTRAINT education_school_fkey FOREIGN KEY (school_id) REFERENCES school(id);


--
-- Name: job_company_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY job
    ADD CONSTRAINT job_company_fkey FOREIGN KEY (company_id) REFERENCES company(id);


--
-- Name: job_prospect_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY job
    ADD CONSTRAINT job_prospect_fkey FOREIGN KEY (prospect_id) REFERENCES prospect(id);


--
-- Name: prospect_industry_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY prospect
    ADD CONSTRAINT prospect_industry_fkey FOREIGN KEY (industry) REFERENCES industry(id);


--
-- Name: prospect_location_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY prospect
    ADD CONSTRAINT prospect_location_fkey FOREIGN KEY (location) REFERENCES location(id);


--
-- Name: prospect_school_school_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY prospect_school
    ADD CONSTRAINT prospect_school_school_fkey FOREIGN KEY (school) REFERENCES school(id);


--
-- Name: prospect_school_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: arachnid
--

ALTER TABLE ONLY prospect_school
    ADD CONSTRAINT prospect_school_user_fkey FOREIGN KEY ("user") REFERENCES prospect(id);


--
-- PostgreSQL database dump complete
--
