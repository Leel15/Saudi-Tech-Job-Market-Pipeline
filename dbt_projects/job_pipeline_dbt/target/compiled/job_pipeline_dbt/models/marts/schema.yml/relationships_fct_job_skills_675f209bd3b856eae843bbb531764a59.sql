
    
    

with child as (
    select skill_key as from_field
    from JOB_MARKET_DB.marts.fct_job_skills
    where skill_key is not null
),

parent as (
    select skill_key as to_field
    from JOB_MARKET_DB.marts.dim_skill
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


