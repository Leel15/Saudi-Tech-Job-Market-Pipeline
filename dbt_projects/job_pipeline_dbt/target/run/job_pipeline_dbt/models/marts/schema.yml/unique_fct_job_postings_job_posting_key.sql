
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    job_posting_key as unique_field,
    count(*) as n_records

from JOB_MARKET_DB.marts.fct_job_postings
where job_posting_key is not null
group by job_posting_key
having count(*) > 1



  
  
      
    ) dbt_internal_test