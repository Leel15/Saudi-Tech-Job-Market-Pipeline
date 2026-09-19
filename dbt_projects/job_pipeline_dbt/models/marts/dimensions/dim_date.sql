{{ config(materialized='table') }}

with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="to_date('2025-01-01')",
        end_date="to_date('2027-12-31')"
    ) }}
)

select
    {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_key,
    date_day,
    extract(day from date_day)      as day_of_month,
    extract(dow from date_day)      as day_of_week,
    to_char(date_day, 'DY')         as day_name,
    extract(month from date_day)    as month,
    to_char(date_day, 'MON')        as month_name,
    extract(quarter from date_day)  as quarter,
    extract(year from date_day)     as year,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from spine