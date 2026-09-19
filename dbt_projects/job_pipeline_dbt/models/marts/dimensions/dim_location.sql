{{ config(materialized='table') }}

with base as (
    select distinct city, country, location
    from {{ ref('int_jobs_enriched') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['city', 'country']) }} as location_key,
    city,
    country,
    location
from base