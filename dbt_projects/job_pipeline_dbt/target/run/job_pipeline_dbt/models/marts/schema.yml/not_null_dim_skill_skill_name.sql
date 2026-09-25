
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select skill_name
from JOB_MARKET_DB.marts.dim_skill
where skill_name is null



  
  
      
    ) dbt_internal_test