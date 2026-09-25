

with base as (
    select distinct city, country, location, city_display
    from JOB_MARKET_DB.intermediate.int_jobs_enriched
)

select
    md5(cast(coalesce(cast(city as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(country as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as location_key,
    city_display as city,
    country,
    location
from base