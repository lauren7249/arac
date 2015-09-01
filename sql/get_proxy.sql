-- Function: get_proxy(text, timestamp without time zone, timestamp without time zone, timestamp without time zone)

-- DROP FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, timestamp without time zone);

CREATE OR REPLACE FUNCTION get_proxy(
    IN target_domain text,
    IN last_rejected_threshold timestamp without time zone,
    IN last_accepted_threshold timestamp without time zone,
    IN timeout_threshold timestamp without time zone,
    OUT proxy text)
  RETURNS text AS
$BODY$
#print_strict_params on
DECLARE
found RECORD;
BEGIN

/* Debug Info */     
RAISE DEBUG 'Input: % % % %', target_domain, last_rejected_threshold, 
  last_accepted_threshold, timeout_threshold;


/* Lock the status table down. Cannot use a SELECT FOR UPDATE with DISTINCT */
LOCK TABLE proxy_domain_status IN ACCESS EXCLUSIVE MODE;


WITH rejects AS
  (SELECT proxy_domain_status.proxy_url AS reject_proxy_url 
  FROM proxy_domain_status 
  WHERE   proxy_domain_status.domain = target_domain AND
    (proxy_domain_status.last_rejected >= last_rejected_threshold::timestamp OR 
      proxy_domain_status.last_accepted >= last_accepted_threshold::timestamp OR in_use)
  ) 
select proxy.url, target_domain as domain
INTO STRICT found 
from proxy 
left join rejects
on reject_proxy_url = proxy.url 
where   reject_proxy_url is null and
  (proxy.last_timeout < timeout_threshold::timestamp OR 
    proxy.last_success > proxy.last_timeout) and
  proxy.consecutive_timeouts < 3 
order by proxy.last_success desc 
limit 1;

proxy := found.url;


BEGIN 
  INSERT INTO proxy_domain_status (proxy_url, domain, in_use) VALUES(found.url, target_domain, TRUE);
EXCEPTION 
  WHEN unique_violation THEN 
    UPDATE proxy_domain_status 
    SET in_use = TRUE::boolean 
    WHERE proxy_url = found.url and domain = target_domain;
END; 

    
EXCEPTION 
   WHEN NO_DATA_FOUND THEN
      RAISE EXCEPTION  'No available proxies for %.', target_domain;
      RETURN;
   WHEN TOO_MANY_ROWS THEN
      RAISE EXCEPTION 'Too many rows returned - this should be impossible!';
   WHEN SQLSTATE '23505' THEN
      /* This is technically a unique key constraint violation and appears in an edge case
         arising from the s.domain = target_domain OR TRUE above but can harmlessly
         be downgraded to a warning.  Practical meaning is no proxies are available */
      RAISE WARNING 'No available proxies.  Please try again.';
      proxy := NULL;
      RETURN;
        
END;
$BODY$
  LANGUAGE plpgsql VOLATILE LEAKPROOF STRICT
  COST 90;
ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, timestamp without time zone)
  OWNER TO arachnid;
