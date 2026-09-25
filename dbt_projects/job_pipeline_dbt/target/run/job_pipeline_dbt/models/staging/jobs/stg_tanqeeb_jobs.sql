
  create or replace   view JOB_MARKET_DB.staging_dbt.stg_tanqeeb_jobs
  
  
  
  
  as (
    with source as (
    select * from JOB_MARKET_DB.STAGING.STG_TANQEEB_JOBS
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
        'tanqeeb'                                as source_name
    from source
)

select * from cleaned
  );

