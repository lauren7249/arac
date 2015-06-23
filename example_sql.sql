SELECT p.id, p.name, p.linkedin_id,
     p.location_raw as location, 
     string_agg(distinct s.name, ', ') as school, string_agg(distinct c.name, ', ') as company, 
     string_agg(distinct j.title,', ') as title, p.industry_raw as industry, 
     translate(p.json->>'skills'::text, '[]"', '') AS skills, 
     string_agg(groups::json->>'name'::text, ', ') as group 
   from prospect p 
     LEFT JOIN job as j on p.id=j.prospect_id 
     LEFT JOIN company as c on j.company_id=c.id 
     LEFT JOIN education as e on e.prospect_id=p.id 
     LEFT JOIN school as s on s.id=e.school_id,
     json_array_elements(p.json->'groups'::text) groups 
     GROUP BY p.id;
