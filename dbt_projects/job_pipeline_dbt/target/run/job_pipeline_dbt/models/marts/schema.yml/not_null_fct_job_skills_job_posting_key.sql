
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select job_posting_key
from JOB_MARKET_DB.marts.fct_job_skills
where job_posting_key is null



  
  
      
    ) dbt_internal_test