
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    company_key as unique_field,
    count(*) as n_records

from JOB_MARKET_DB.marts.dim_company
where company_key is not null
group by company_key
having count(*) > 1



  
  
      
    ) dbt_internal_test