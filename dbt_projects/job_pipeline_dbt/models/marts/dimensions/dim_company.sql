{{ config(materialized='table') }}

with base as (
    select distinct company
    from {{ ref('int_jobs_enriched') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['company']) }} as company_key,
    company as company_name
from base