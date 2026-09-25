

with base as (
    select distinct skill
    from JOB_MARKET_DB.intermediate.int_job_skills
)

select
    md5(cast(coalesce(cast(skill as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as skill_key,
    skill as skill_name
from base