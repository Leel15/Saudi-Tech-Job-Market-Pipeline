select * from JOB_MARKET_DB.staging_dbt.stg_jooble_jobs
union all
select * from JOB_MARKET_DB.staging_dbt.stg_jsearch_jobs
union all
select * from JOB_MARKET_DB.staging_dbt.stg_freehire_jobs
union all
select * from JOB_MARKET_DB.staging_dbt.stg_tanqeeb_jobs
union all
select * from JOB_MARKET_DB.staging_dbt.stg_tapneo_jobs