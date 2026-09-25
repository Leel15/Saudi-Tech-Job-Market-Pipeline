
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select source_count
from JOB_MARKET_DB.marts.fct_job_postings
where source_count is null



  
  
      
    ) dbt_internal_test