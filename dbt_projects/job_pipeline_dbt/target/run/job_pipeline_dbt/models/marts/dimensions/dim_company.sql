
  
    

create or replace transient table JOB_MARKET_DB.marts.dim_company
    
    
    
    
    

    as (

with base as (
    select distinct company
    from JOB_MARKET_DB.intermediate.int_jobs_enriched
)

select
    md5(cast(coalesce(cast(company as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as company_key,
    company as company_name
from base
    )
;


  