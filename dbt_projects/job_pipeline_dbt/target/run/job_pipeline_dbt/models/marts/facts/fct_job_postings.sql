
  
    

create or replace transient table JOB_MARKET_DB.marts.fct_job_postings
    
    
    
    
    

    as (-- Grain: صف واحد لكل إعلان وظيفي فريد
-- (company + city + country + location + title، مطابق تمامًا لمعيار int_jobs_deduplicated)


with base as (
    select * from JOB_MARKET_DB.intermediate.int_jobs_enriched
)

select
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(city as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(country as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(location as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(title as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as job_posting_key,
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))                  as company_key,
    md5(cast(coalesce(cast(city as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(country as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))          as location_key,
    md5(cast(coalesce(cast(employment_type as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(education as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(seniority_level as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(job_category as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as job_attributes_key,
    md5(cast(coalesce(cast(posted_date as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT))              as date_key,
    title,
    url,
    seen_on_sources,
    source_count,
    1 as job_posting_count
from base
    )
;


  