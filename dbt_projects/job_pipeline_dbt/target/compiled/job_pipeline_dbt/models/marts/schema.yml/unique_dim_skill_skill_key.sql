
    
    

select
    skill_key as unique_field,
    count(*) as n_records

from JOB_MARKET_DB.marts.dim_skill
where skill_key is not null
group by skill_key
having count(*) > 1


