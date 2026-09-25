
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select title
from JOB_MARKET_DB.intermediate.int_jobs_deduplicated
where title is null



  
  
      
    ) dbt_internal_test