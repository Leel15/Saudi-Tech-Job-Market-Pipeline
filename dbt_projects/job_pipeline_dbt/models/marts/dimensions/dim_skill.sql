{{ config(materialized='table') }}

with base as (
    select distinct skill
    from {{ ref('int_job_skills') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['skill']) }} as skill_key,
    skill as skill_name
from base