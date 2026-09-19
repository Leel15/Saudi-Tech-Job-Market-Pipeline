{{ config(materialized='table') }}

with base as (
    select distinct company
    from {{ ref('int_jobs_enriched') }}
    where company is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['company']) }} as company_key,
    company as company_name
from base