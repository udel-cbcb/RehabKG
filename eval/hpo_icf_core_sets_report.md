# HPO→ICF reachability vs ICF Core Sets

Read-only evaluation; this report does not alter graph edges.

The curated register `curated/icf_core_sets.csv` is empty. No ICF
Core Set category lists were supplied, so per-core-set recall cannot
yet be evaluated. Add source-backed categories only after confirming
their redistribution terms.

Live graph metrics were not collected in this report snapshot because the
command environment lacked `NEO4J_PASSWORD`; the zero values from that run are
not graph counts. Run `python scripts/eval_hpo_icf_vs_core_sets.py` in an
environment with Neo4j credentials to collect read-only metrics. The matcher
has not been changed.
