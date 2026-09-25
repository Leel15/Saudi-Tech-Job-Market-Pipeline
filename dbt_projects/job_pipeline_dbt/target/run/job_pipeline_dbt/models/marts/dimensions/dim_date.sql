
  
    

create or replace transient table JOB_MARKET_DB.marts.dim_date
    
    
    
    
    

    as (

with spine as (
    





with rawdata as (

    

    

    with p as (
        select 0 as generated_number union all select 1
    ), unioned as (

    select

    
    p0.generated_number * power(2, 0)
     + 
    
    p1.generated_number * power(2, 1)
     + 
    
    p2.generated_number * power(2, 2)
     + 
    
    p3.generated_number * power(2, 3)
     + 
    
    p4.generated_number * power(2, 4)
     + 
    
    p5.generated_number * power(2, 5)
     + 
    
    p6.generated_number * power(2, 6)
     + 
    
    p7.generated_number * power(2, 7)
     + 
    
    p8.generated_number * power(2, 8)
     + 
    
    p9.generated_number * power(2, 9)
     + 
    
    p10.generated_number * power(2, 10)
    
    
    + 1
    as generated_number

    from

    
    p as p0
     cross join 
    
    p as p1
     cross join 
    
    p as p2
     cross join 
    
    p as p3
     cross join 
    
    p as p4
     cross join 
    
    p as p5
     cross join 
    
    p as p6
     cross join 
    
    p as p7
     cross join 
    
    p as p8
     cross join 
    
    p as p9
     cross join 
    
    p as p10
    
    

    )

    select *
    from unioned
    where generated_number <= 1460
    order by generated_number



),

all_periods as (

    select (
        

    dateadd(
        day,
        row_number() over (order by generated_number) - 1,
        to_date('2024-01-01')
        )


    ) as date_day
    from rawdata

),

filtered as (

    select *
    from all_periods
    where date_day <= to_date('2027-12-31')

)

select * from filtered


),

calendar as (
    select
        md5(cast(coalesce(cast(date_day as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as date_key,
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
        md5(cast(coalesce(cast(null::date as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as date_key,
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
    )
;


  