{{ config(materialized='table') }}

with base as (
    select distinct city, country, location, city_display
    from {{ ref('int_jobs_enriched') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['city', 'country']) }} as location_key,
    city_display as city,
    country,
    location
from base