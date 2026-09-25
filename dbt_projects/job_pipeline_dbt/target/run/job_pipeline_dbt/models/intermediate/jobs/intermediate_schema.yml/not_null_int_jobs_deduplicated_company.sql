
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select company
from JOB_MARKET_DB.intermediate.int_jobs_deduplicated
where company is null



  
  
      
    ) dbt_internal_test