
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select title
from JOB_MARKET_DB.staging_dbt.stg_tanqeeb_jobs
where title is null



  
  
      
    ) dbt_internal_test