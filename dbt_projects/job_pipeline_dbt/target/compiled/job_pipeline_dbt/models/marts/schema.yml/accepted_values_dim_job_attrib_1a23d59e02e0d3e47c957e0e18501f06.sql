
    
    

with all_values as (

    select
        employment_type as value_field,
        count(*) as n_records

    from JOB_MARKET_DB.marts.dim_job_attributes
    group by employment_type

)

select *
from all_values
where value_field not in (
    'Full-time','Part-time','Contract','Internship','Temporary','Not Specified'
)


