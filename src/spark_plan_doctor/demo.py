from __future__ import annotations

SAMPLE_PLAN = """
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[order_date#12], functions=[count(1)])
   +- Exchange hashpartitioning(order_date#12, 200), ENSURE_REQUIREMENTS
      +- HashAggregate(keys=[order_date#12], functions=[partial_count(1)])
         +- Project [order_date#12, customer_id#18]
            +- SortMergeJoin [customer_id#18], [customer_id#41], Inner
               :- Sort [customer_id#18 ASC NULLS FIRST], false, 0
               :  +- Exchange hashpartitioning(customer_id#18, 200), ENSURE_REQUIREMENTS
               :     +- FileScan parquet bronze.orders[order_date#12,customer_id#18] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[dbfs:/mnt/bronze/orders], PartitionFilters: [], PushedFilters: [], ReadSchema: struct<order_date:string,customer_id:string>
               +- Sort [customer_id#41 ASC NULLS FIRST], false, 0
                  +- Exchange hashpartitioning(customer_id#41, 200), ENSURE_REQUIREMENTS
                     +- BatchEvalPython [normalize(customer_id#41)#90], [pythonUDF0#91]
                        +- FileScan parquet silver.customers[customer_id#41] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[dbfs:/mnt/silver/customers], PartitionFilters: [], PushedFilters: [], ReadSchema: struct<customer_id:string>
"""


def sample_plan() -> str:
    return SAMPLE_PLAN.strip()
