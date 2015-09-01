delete from bing_searches where intitle in (
select max(a.intitle) as upper_intitle
from bing_searches a inner join bing_searches b on lower(b.intitle)=lower(a.intitle) where a.intitle != b.intitle
group by lower(b.intitle));

alter table bing_searches alter column intitle type citext;