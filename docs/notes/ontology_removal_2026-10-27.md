# Ontology removal from live graph

On 2026-10-27, at the user's request, 12 ontology source groups were removed
from live Neo4j with their incident relationships: MELLO-D, TRAK, FRMO, BCIO,
BCTT, STO, PACO, MSO, POEM, PHENX, NIHSS, and ACVD. PMR, OPE, PHY, and
ONTOLOCO were **not** removed in this cleanup, although their exact licences
remain flagged for review. A later read-only inventory also found PMR,
MELLO-D, and REHABO absent from this live graph; these were not part of the
requested deletion. No dataset nodes were
removed. Verification found zero remaining nodes
from those source labels and zero relationships incident to them.

The backup is `deliverables/public-graph-removal-backup-2026-10-27.json`.
Default Cypher and bulk loading/export code no longer includes the removed
ontology families or their curated bridge files. Source OWL files remain local
and untouched; they are not loaded by default. Tests now describe the retained
graph rather than expecting removed ontology nodes.

This cleanup is not a legal determination that every remaining source is safe
to publish. See `docs/notes/data_hosting_license_audit.md` for the remaining
conditions and `docs/notes/public_hosting_allowlist.md` for the proposed
reviewable source scope.

## Follow-up focused refresh (2026-11-05)

The focused refresh removed COPPER, KHMO, CBHA (including its 1,210 activity
nodes), and the other flagged ontology families, while refreshing REHABO, ICF,
EXMO, PAIN, Mondo, and the existing 10,000-node Uberon subset. HPO was restored
from staged `hp.owl` after an initial refresh implementation removed it; nine
explicit HPO→ICF links were recreated with curated, unreviewed provenance.
Clinical/dataset nodes remain. Final counts and hashes are recorded in
`eval/public_ontology_refresh_manifest.json`.

The default Cypher and bulk ontology builders were subsequently reconciled to
the focused source selection and use `bridge_default_sources`; the experimental
extractor functions remain in the code.

**Update (2026-11-05):** the focused refresh is now deterministic (Uberon/Mondo
subsets are sorted before slicing) and covered by the opt-in E2E pipeline test.
The live `neo4j` graph was loaded from a dump of the E2E `test` database and
matches its snapshot. Full Cypher-vs-bulk parity remains unverified.

**Update (2026-11-06):** full generated-CSV `neo4j-admin` parity is now verified
by the opt-in `tests/test_bulk_parity.py` against
`eval/bulk_parity_baseline.json`. It matches the focused snapshot on all
node/label/source counts, bridge/clinical relationship counts, and gold 35/35;
`SUBCLASS_OF` remains out of scope because the bulk path also emits
source-owned Mondo/Uberon/HPO/EXMO hierarchy.
