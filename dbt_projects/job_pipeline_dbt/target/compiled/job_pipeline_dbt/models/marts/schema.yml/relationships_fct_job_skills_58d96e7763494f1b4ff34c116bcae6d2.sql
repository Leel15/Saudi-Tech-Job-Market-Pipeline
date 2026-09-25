
    
    

with child as (
    select job_posting_key as from_field
    from JOB_MARKET_DB.marts.fct_job_skills
    where job_posting_key is not null
),

parent as (
    select job_posting_key as to_field
    from JOB_MARKET_DB.marts.fct_job_postings
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


