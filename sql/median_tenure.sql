with tenures as 
(select * from job where end_date is not null and start_date is not null limit 10000)
select median((DATE_PART('YEAR',end_date)-DATE_PART('YEAR',start_date))::numeric) from tenures

select * from bing_searches where terms='Yesenia miranda california' or true
