-- Function: get_proxy(text, timestamp without time zone, timestamp without time zone, interval)

-- DROP FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval);

CREATE OR REPLACE FUNCTION get_proxy(
    IN target_domain text,
    IN last_rejected_threshold timestamp without time zone,
    IN last_accepted_threshold timestamp without time zone,
    IN retry_interval interval DEFAULT '2 days'::interval day,
    OUT proxy text)
  RETURNS text AS
$BODY$
#print_strict_params on
DECLARE
found RECORD;
timeout_threshold timestamp without time zone;
BEGIN

/* Debug Info */     
RAISE DEBUG 'Input: % % % %', target_domain, last_rejected_threshold, 
    last_accepted_threshold, timeout_threshold;
/* Debug Info */

/* Check for invalid input */
IF last_rejected_threshold >= last_accepted_threshold THEN
    RAISE EXCEPTION 'last_rejected_threshold cannot be LATER THAN last_accepted_threshold';
END IF;

/* Calculate the timeout_threshold */
timeout_threshold := NOW() - retry_interval;

/* Lock the status table down. Cannot use a SELECT FOR UPDATE with DISTINCT */
LOCK TABLE proxy_domain_status IN ACCESS EXCLUSIVE MODE;

/* Look for an available url to use */
SELECT p.url AS url, s.domain as last_domain, 
        target_domain AS target 
    INTO STRICT found 
   FROM proxy AS p
      RIGHT JOIN (SELECT DISTINCT ON (proxy_url) * from proxy_domain_status 
    WHERE in_use = FALSE) s 
           ON (p.url=s.proxy_url) 
           WHERE
           (s.last_rejected <= last_rejected_threshold::timestamp
             OR s.last_accepted >= last_accepted_threshold::timestamp)
        AND (
             /* This catches cases where the 'right' side of the join does not have an entry */
             s.domain = target_domain OR TRUE::boolean 
       AND p.consecutive_timeouts < 3
           AND (p.last_timeout <= timeout_threshold::timestamp
               OR p.last_success > p.last_timeout::timestamp)
        )
     ORDER BY p.last_success DESC LIMIT 1;

proxy := found.url;
     
/* Debug Info */ 
RAISE DEBUG 'Found Row: %', found;
RAISE DEBUG 'Found InUse: %', found.in_use; 
RAISE DEBUG 'Found Proxy: %', found.url;   
/* Debug Info */

/* We're still in a transaction, so let's update the status table to check out a proxy */
UPDATE proxy_domain_status 
    SET domain = target_domain,
        in_use = TRUE::boolean 
        WHERE proxy_url = found.url;
        
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
ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) SET log_min_duration_statement='100';

ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) SET log_lock_waits='on';

ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) SET deadlock_timeout='1000';

ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) SET default_transaction_isolation='repeatable read';

ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) SET lock_timeout='5000';

ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) SET application_name='scraper';

ALTER FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval)
  OWNER TO arachnid;
COMMENT ON FUNCTION get_proxy(text, timestamp without time zone, timestamp without time zone, interval) IS 'Use to return an available proxy for a domain.

Call as 
SELECT get_proxy(target_domain::text, last_rejected::timestamp, last_accepted::timestamp, retry_interval::INTERVAL DEFAULT 2 DAYS);';