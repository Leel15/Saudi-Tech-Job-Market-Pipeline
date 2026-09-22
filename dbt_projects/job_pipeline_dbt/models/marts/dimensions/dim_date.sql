{{ config(materialized='table') }}

with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="to_date('2024-01-01')",
        end_date="to_date('2027-12-31')"
    ) }}
),

calendar as (
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
),

unknown as (
    select
        {{ dbt_utils.generate_surrogate_key(['null::date']) }} as date_key,
        null::date as date_day,
        null as day_of_month,
        null as day_of_week,
        'Unknown' as day_name,
        null as month,
        'Unknown' as month_name,
        null as quarter,
        null as year,
        null as is_weekend
)

select * from calendar
union all
select * from unknown