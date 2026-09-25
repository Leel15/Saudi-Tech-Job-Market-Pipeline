
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select location_key as from_field
    from JOB_MARKET_DB.marts.fct_job_postings
    where location_key is not null
),

parent as (
    select location_key as to_field
    from JOB_MARKET_DB.marts.dim_location
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test