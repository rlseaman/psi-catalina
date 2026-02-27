# psi-catalina — Claude Project Context

## What this repository is

CSS-maintained fork of [sbn-psi/catalina](https://github.com/sbn-psi/catalina),
the Python pipeline that PSI uses to ingest and validate CSS data products into
the PDS archive.

**Upstream:** `https://github.com/sbn-psi/catalina` (remote name: `upstream`)
**CSS fork:** `https://github.com/rlseaman/psi-catalina` (remote name: `origin`)
**Local path:** `~/Claude/SBN-PSI/catalina/`
**Language:** Python 3.7+ (pipeline); schemas are XML

## Scope of changes in this fork

CSS adds performance improvements and infrastructure that we hope PSI will adopt.
All CSS changes are documented in `CHANGES.md`.  Changes that are CSS-specific
and not suitable for PSI upstream live in `rlseaman/CSS_PDS4_tools` instead.

**In scope for this repo:**
- Parallelism improvements to the validate orchestration layer
- PDS4 schema files and a portable OASIS XML catalog for offline validation
- Canary injection system (planned)
- Reporting accuracy fixes (planned)

**Not in scope:**
- The validate engine itself → `rlseaman/css-validate`
- CSS operational benchmark scripts → `rlseaman/CSS_PDS4_tools`
- CSS label generation tools → `rlseaman/CSS_PDS4_tools`

## Key files

| File | Purpose |
|------|---------|
| `ingest/process_uploads.py` | Top-level orchestration; parallel batch dispatch |
| `ingest/validation.py` | validate subprocess invocation; parallel funpack |
| `ingest/options.py` | CLI flags including `--parallel-batches`, `--funpack-workers` |
| `ingest/product.py` | Product/ObsNight data model |
| `ingest/paths.py` | Archive path conventions |
| `ingest/preflight.py` | Pre-validation file checks |
| `schemas/catalog_all.xml` | OASIS XML catalog → local PDS4 schema files |
| `schemas/PDS4_*.xsd/.sch` | Local copies of all needed PDS4 schemas (1G00, 1N00) |
| `CHANGES.md` | Full record of every CSS-local modification |

## Production invocation (what PSI runs)

```bash
validate -s json -E 2147483647 \
  -C /path/to/schemas/catalog_all.xml \
  -t <target_dir>
```

No `-D` flag: content validation is enabled.  CSS uses the same flags.

## How CSS adds parallelism

```bash
# Recommended for bulk backlog (4 concurrent JVMs, 4 funpack workers each)
process_uploads.py --parallel-batches 4 --funpack-workers 4 ...

# Maximum throughput (disk I/O limited beyond this on spinning disk)
process_uploads.py --parallel-batches 8 --funpack-workers 4 ...
```

Both flags default to 1, preserving PSI's original sequential behaviour.

## Archive structure (CSS side)

```
/archive/{INST}/{YEAR}/{DATE}/              data files (*.arch.fz, *.calb.fz, ...)
/archive/{INST}/{YEAR}/other/pds4/{DATE}/  PDS4 labels (*.arch.xml, *.calb.xml, ...)
```

Instruments: G96 (ML 1.5m 10K CCD), I52, 703, E12, V06, V00, G84

## Related repositories

| Repo | What it is |
|------|-----------|
| `rlseaman/css-validate` | Fork of NASA-PDS/validate with Java fast path |
| `rlseaman/CSS_PDS4_tools` | CSS label generation + operational benchmark tools |
| `NASA-PDS/validate` | Upstream validate engine |
| `sbn-psi/catalina` | Upstream pipeline (this repo's upstream) |

## Working notes

Detailed benchmark results, nightly run analyses, and open issues are in the
SBN-PSI working directory (`~/Claude/SBN-PSI/`), specifically:
- `NOTES.md` — canonical session record
- `css-validate-plan-2026-02-27.md` — strategic plan
- `validate-night-issues-2026-02-26.md` — known bugs (count discrepancy, model files)
