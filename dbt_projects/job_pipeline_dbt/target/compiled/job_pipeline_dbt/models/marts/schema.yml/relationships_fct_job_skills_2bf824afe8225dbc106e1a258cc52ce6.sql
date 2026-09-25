
    
    

with child as (
    select company_key as from_field
    from JOB_MARKET_DB.marts.fct_job_skills
    where company_key is not null
),

parent as (
    select company_key as to_field
    from JOB_MARKET_DB.marts.dim_company
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


