with base as (
    select
        company,
        city,
        country,
        title,
        job_category,
        seniority_level,
        employment_type,
        education,
        skills
    from {{ ref('int_jobs_enriched') }}
    where skills is not null
),

split as (
    select
        base.company,
        base.city,
        base.country,
        base.title,
        base.job_category,
        base.seniority_level,
        base.employment_type,
        base.education,
        trim(s.value) as skill
    from base,
    lateral split_to_table(base.skills, ',') as s
)

select * from split
where skill != ''