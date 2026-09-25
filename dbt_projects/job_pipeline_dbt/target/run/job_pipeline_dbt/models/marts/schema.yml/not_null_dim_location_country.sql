
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select country
from JOB_MARKET_DB.marts.dim_location
where country is null



  
  
      
    ) dbt_internal_test