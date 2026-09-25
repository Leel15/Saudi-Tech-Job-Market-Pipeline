
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select company
from JOB_MARKET_DB.staging_dbt.stg_tapneo_jobs
where company is null



  
  
      
    ) dbt_internal_test