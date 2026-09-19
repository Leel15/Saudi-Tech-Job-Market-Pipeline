-- Junk dimension: يجمع 4 خصائص منخفضة التنوع كانت كل واحدة لحالها
-- "بُعد بعمود واحد" (ممنوع حسب المنهجية)، فتجميعها هنا يصير بُعد حقيقي.
{{ config(materialized='table') }}

with base as (
    select distinct
        employment_type,
        education,
        seniority_level,
        job_category
    from {{ ref('int_jobs_enriched') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'employment_type', 'education', 'seniority_level', 'job_category'
    ]) }} as job_attributes_key,
    employment_type,
    education,
    seniority_level,
    job_category
from base