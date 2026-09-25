
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    location_key as unique_field,
    count(*) as n_records

from JOB_MARKET_DB.marts.dim_location
where location_key is not null
group by location_key
having count(*) > 1



  
  
      
    ) dbt_internal_test