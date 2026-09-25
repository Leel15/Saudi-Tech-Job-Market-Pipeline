
  create or replace   view JOB_MARKET_DB.intermediate.int_jobs_enriched
  
  
  
  
  as (
    with base as (
    select * from JOB_MARKET_DB.intermediate.int_jobs_deduplicated
),

enriched as (
    select
        *,
        coalesce(city, 'Not Specified') as city_display,

        case
            when lower(title) like '%senior%' or lower(title) like '%lead%'
                 or lower(title) like '%principal%' or lower(title) like '%head of%'
                then 'Senior'
            when lower(title) like '%junior%' or lower(title) like '%intern%'
                 or lower(title) like '%entry%'
                then 'Junior'
            when lower(title) like '%manager%' or lower(title) like '%director%'
                then 'Management'
            else 'Mid/Unspecified'
        end as seniority_level,

        case
            when lower(title) like '%data%' or lower(title) like '%analyst%'
                 or lower(title) like '%scientist%'
                then 'Data'
            when lower(title) like '%security%' or lower(title) like '%cyber%'
                then 'Security'
            when lower(title) like '%devops%' or lower(title) like '%cloud%'
                 or lower(title) like '%infrastructure%'
                then 'DevOps/Infrastructure'
            when lower(title) like '%developer%' or lower(title) like '%engineer%'
                 or lower(title) like '%backend%' or lower(title) like '%frontend%'
                then 'Software Engineering'
            when lower(title) like '%design%' or lower(title) like '%ux%'
                 or lower(title) like '%ui%'
                then 'Design'
            else 'Other/Unspecified'
        end as job_category

    from base
)

select * from enriched
  );

