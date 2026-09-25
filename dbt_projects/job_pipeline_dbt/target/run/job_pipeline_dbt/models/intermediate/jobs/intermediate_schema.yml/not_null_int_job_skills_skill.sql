
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select skill
from JOB_MARKET_DB.intermediate.int_job_skills
where skill is null



  
  
      
    ) dbt_internal_test