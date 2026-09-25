-- Bridge (factless) fact table. Grain: صف واحد لكل زوج (إعلان وظيفي، مهارة)
-- job_posting_key مطابق تمامًا لنفس تركيبة fct_job_postings لضمان صحة العلاقة بينهما


with base as (
    select * from JOB_MARKET_DB.intermediate.int_job_skills
)

select
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(city as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(country as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(location as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(title as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as job_posting_key,
    md5(cast(coalesce(cast(skill as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))                    as skill_key,
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))                  as company_key,
    md5(cast(coalesce(cast(city as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(country as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))          as location_key,
    md5(cast(coalesce(cast(employment_type as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(education as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(seniority_level as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(job_category as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as job_attributes_key,
    md5(cast(coalesce(cast(posted_date as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))              as date_key
from base