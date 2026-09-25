





with validation_errors as (

    select
        company, city, title
    from JOB_MARKET_DB.intermediate.int_jobs_deduplicated
    group by company, city, title
    having count(*) > 1

)

select *
from validation_errors


