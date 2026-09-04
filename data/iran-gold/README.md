# Iran Melted Gold Data

## Sources named by the canonical map

### Primary intraday format

`general-platforms` CSV is described by the canonical map as the current reliable intraday format. A real sample/schema has not yet been added to this repository.

### Cross-check source

TGJU — melted-gold price pages — is designated as an independent realtime cross-check. The map states that a documented public API is not available and automated access would therefore require page extraction.

## Required dataset metadata

Every imported dataset must record:

- instrument/market label
- provider
- file/source identifier
- timezone
- timestamp unit/format
- start/end time
- latest valid cutoff
- OHLC/tick field definitions
- price unit
- missing records
- duplicates
- forming/closed-bar handling
- transformation history

## Storage rule

Raw large datasets remain local or in an external data store by default. Repository commits should contain schemas, checksums, manifests, validation reports and small authorized samples rather than uncontrolled raw dumps.

## Status

`general-platforms` schema: **missing input**.
TGJU extraction connector: **not built**.
