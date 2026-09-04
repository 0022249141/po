# Historical Asset Recovery Protocol

Use this protocol for artifacts named by the canonical Resource Connector Map but not present in the repository.

## Recovery evidence accepted

An item may move from `missing` to `recovered` only with at least one of:

- exact original file supplied by the user;
- exact repository path and commit containing the artifact;
- trusted connector/file reference resolving to the exact artifact;
- user-provided canonical content explicitly designated as the replacement source of truth.

## On recovery

1. Compute SHA-256 when bytes are available.
2. Record filename/path, source, version/date and recovery method.
3. Preserve the original file unchanged in the approved storage layer.
4. Create a normalized/curated derivative separately.
5. Link derivative back to the original provenance record.
6. Update `docs/MISSING_ASSETS.md` and source/pipeline registry.

## Prohibited

- guessing acronym expansions;
- generating a replacement under the exact historic filename and calling it recovered;
- silently correcting or merging conflicting versions;
- using web paraphrases as proof of the user's original file content.
