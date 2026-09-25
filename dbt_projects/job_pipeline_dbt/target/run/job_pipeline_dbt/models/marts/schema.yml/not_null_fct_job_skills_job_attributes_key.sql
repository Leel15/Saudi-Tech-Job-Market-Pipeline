
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select job_attributes_key
from JOB_MARKET_DB.marts.fct_job_skills
where job_attributes_key is null



  
  
      
    ) dbt_internal_test