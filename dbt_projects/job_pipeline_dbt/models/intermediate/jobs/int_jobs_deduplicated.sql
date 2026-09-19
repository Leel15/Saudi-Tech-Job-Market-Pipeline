-- معيار التكرار: company + city + title
-- (لا يوجد first_seen/last_seen/repost_count بجداول Snowflake الفعلية)

with base as (
    select * from {{ ref('int_all_jobs') }}
),

grouped as (
    select
        company,
        city,
        country,
        location,
        title,
        listagg(distinct source_name, ', ')  as seen_on_sources,
        count(distinct source_name)          as source_count,
        max(description)                     as description,
        max(skills)                          as skills,
        max(employment_type)                 as employment_type,
        max(education)                       as education,
        max(url)                             as url,
        max(posted_date)                     as posted_date
    from base
    group by company, city, country, location, title
)

select * from grouped