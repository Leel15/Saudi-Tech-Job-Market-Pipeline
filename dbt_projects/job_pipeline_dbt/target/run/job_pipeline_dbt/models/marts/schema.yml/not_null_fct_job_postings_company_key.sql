
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select company_key
from JOB_MARKET_DB.marts.fct_job_postings
where company_key is null



  
  
      
    ) dbt_internal_test