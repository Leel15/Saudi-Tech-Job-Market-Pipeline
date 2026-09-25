
    
    

select
    job_attributes_key as unique_field,
    count(*) as n_records

from JOB_MARKET_DB.marts.dim_job_attributes
where job_attributes_key is not null
group by job_attributes_key
having count(*) > 1


