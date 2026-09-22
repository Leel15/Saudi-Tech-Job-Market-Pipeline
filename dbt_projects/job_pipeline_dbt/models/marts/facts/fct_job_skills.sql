{{ config(materialized='table') }}

with base as (
    select * from {{ ref('int_job_skills') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['company', 'city', 'title']) }} as job_posting_key,
    {{ dbt_utils.generate_surrogate_key(['skill']) }}                    as skill_key,
    {{ dbt_utils.generate_surrogate_key(['company']) }}                  as company_key,
    {{ dbt_utils.generate_surrogate_key(['city', 'country']) }}          as location_key,
    {{ dbt_utils.generate_surrogate_key(['employment_type','education','seniority_level','job_category']) }} as job_attributes_key,
    {{ dbt_utils.generate_surrogate_key(['posted_date']) }}              as date_key
from base