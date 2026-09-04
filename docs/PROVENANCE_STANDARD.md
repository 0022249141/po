# Provenance Standard

## Source artifact record

Minimum fields:

- artifact/source id
- original title/filename
- author/publisher/source
- canonical URL/path
- version/date
- retrieval date
- retrieval method
- license/storage policy if known
- checksum when bytes are stored
- transformation history
- derived-note links

## Dataset record

Use `data/schema/dataset_manifest.schema.json` and `tools/init_manifest.py`.

## Derived knowledge record

A generated or normalized note must link to one or more `source_id` values. If it is a synthesis rather than source definition, mark it `generated: true` and choose the correct evidence class.

## Backtest record

A backtest is reproducible only when the run record identifies:

- frozen spec id/version
- code commit
- dataset id/checksum
- execution assumptions
- run parameters
- IS/OOS role
- output metrics/artifacts

## Hash policy

SHA-256 identifies bytes, not semantic truth. A matching hash proves file identity relative to the recorded copy; it does not validate data quality or source claims.
