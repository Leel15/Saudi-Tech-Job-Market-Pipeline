select * from {{ ref('stg_jooble_jobs') }}
union all
select * from {{ ref('stg_jsearch_jobs') }}
union all
select * from {{ ref('stg_freehire_jobs') }}
union all
select * from {{ ref('stg_tanqeeb_jobs') }}
union all
select * from {{ ref('stg_tapneo_jobs') }}