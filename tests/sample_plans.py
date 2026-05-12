SAMPLE_PLAN = """
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [order_date#12, customer_id#18]
   +- SortMergeJoin [customer_id#18], [customer_id#41], Inner
      :- Sort [customer_id#18 ASC NULLS FIRST], false, 0
      :  +- Exchange hashpartitioning(customer_id#18, 200), ENSURE_REQUIREMENTS
      :     +- FileScan parquet bronze.orders[order_date#12,customer_id#18] Batched: true, PartitionFilters: [], PushedFilters: [], ReadSchema: struct<order_date:string,customer_id:string>
      +- Sort [customer_id#41 ASC NULLS FIRST], false, 0
         +- Exchange hashpartitioning(customer_id#41, 200), ENSURE_REQUIREMENTS
            +- BatchEvalPython [normalize(customer_id#41)#90], [pythonUDF0#91]
               +- FileScan parquet silver.customers[customer_id#41] Batched: true, PartitionFilters: [], PushedFilters: [], ReadSchema: struct<customer_id:string>
""".strip()

CARTESIAN_PLAN = """
== Physical Plan ==
+- CartesianProduct
   :- FileScan parquet left_table[id#1] PartitionFilters: [], PushedFilters: []
   +- FileScan parquet right_table[id#2] PartitionFilters: [], PushedFilters: []
""".strip()
