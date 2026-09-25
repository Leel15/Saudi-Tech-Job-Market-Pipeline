with base as (
    select
        company,
        city,
        country,
        location,
        title,
        job_category,
        seniority_level,
        employment_type,
        education,
        posted_date,
        skills
    from JOB_MARKET_DB.intermediate.int_jobs_enriched
    where skills is not null
),

split as (
    select
        base.company,
        base.city,
        base.country,
        base.location,
        base.title,
        base.job_category,
        base.seniority_level,
        base.employment_type,
        base.education,
        base.posted_date,
        trim(s.value) as raw_skill
    from base,
    lateral split_to_table(base.skills, ',') as s
),

normalized as (
    select
        split.company,
        split.city,
        split.country,
        split.location,
        split.title,
        split.job_category,
        split.seniority_level,
        split.employment_type,
        split.education,
        split.posted_date,
        coalesce(syn.canonical_skill, split.raw_skill) as skill
    from split
    left join JOB_MARKET_DB.PUBLIC.skill_synonyms as syn
        on lower(trim(split.raw_skill)) = lower(trim(syn.raw_skill))
)

select * from normalized
where skill != ''