with source as (
    select * from {{ source('job_market_staging', 'STG_JOOBLE_JOBS') }}
),

cleaned as (
    select
        trim(job_title)                     as title,
        coalesce(trim(initcap(company_name)), 'Unknown Company') as company,
        city,
        country,
        case
            when city is not null then city || ', ' || country
            else country
        end                                   as location,
        try_to_date(posted_date)             as posted_date,
        employment_type,
        education,
        job_description                        as description,
        skills,
        job_url                                as url,
        'jooble'                                as source_name
    from source
)

select * from cleaned