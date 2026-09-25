-- Junk dimension: يجمع 4 خصائص منخفضة التنوع كانت كل واحدة لحالها
-- "بُعد بعمود واحد" (ممنوع حسب المنهجية)، فتجميعها هنا يصير بُعد حقيقي.


with base as (
    select distinct
        employment_type,
        education,
        seniority_level,
        job_category
    from JOB_MARKET_DB.intermediate.int_jobs_enriched
)

select
    md5(cast(coalesce(cast(employment_type as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(education as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(seniority_level as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(job_category as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as job_attributes_key,
    coalesce(employment_type, 'Not Specified') as employment_type,
    coalesce(education, 'Not Specified')       as education,
    seniority_level,
    job_category
from base