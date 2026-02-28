# CSS-Local Changes to sbn-psi/catalina

This file documents every deviation from the upstream
[sbn-psi/catalina](https://github.com/sbn-psi/catalina) source tree.

These changes were developed by CSS (Catalina Sky Survey) to improve throughput
for bulk backlog processing and to support CSS deployment environments.  They
are offered back to PSI for adoption; PSI is under no obligation to merge them.

---

## Python 3.7 compatibility

**Files:** all modules under `ingest/`
**Commit:** `ec90e7c`

Added `from __future__ import annotations` (PEP 563) to every pipeline module.
This allows Python 3.7 to accept the newer-style type hints (`list[X]`, `X | Y`,
etc.) already present throughout the codebase.  Zero behaviour change in Python
3.9 and later.

Background: CSS operates one deployment (sikhote, RHEL 8) on Anaconda Python
3.7.6.  A Python 3.11 conda environment has been created and verified; switching
the pipeline activation is pending.  The `from __future__` lines are harmless
once 3.11 is active and can be removed at PSI's discretion.

---

## Local PDS4 schema files and portable OASIS XML catalog

**Directory:** `schemas/`
**Commit:** `8e0c192`

Added local copies of all PDS4 XSD schema and Schematron rule files needed
for CSS label validation, covering IM versions 1G00 (1.16.0.0) and 1N00
(1.23.0.0).  Source: https://github.com/sbn-psi/pds4-schema-files

The OASIS XML catalog (`schemas/catalog_all.xml`) maps PDS4 namespace URLs
to these local files, eliminating all network fetches during validation.
Pass it to validate with:

```
validate -C /absolute/path/to/schemas/catalog_all.xml ...
```

**Portability fix:** The original catalog used hardcoded absolute paths
(`file:///home/seaman/...`).  The committed version uses relative URIs
(`rewritePrefix="./"`) per OASIS XML Catalogs 1.1 §7.1.2, resolving
correctly on any machine without manual editing.

`schemas/urls.txt` records the original download URLs for each schema file.
`schemas/validate.sh` is an older pre-catalog invocation style (uses explicit
`-x`/`-S` flags rather than `-C`); retained for reference but superseded by
the catalog approach.

---

## Parallel batch execution and parallel funpack decompression

**Files:** `ingest/options.py`, `ingest/process_uploads.py`, `ingest/validation.py`
**Commits:** `ec90e7c`, `df9d908`

### `--parallel-batches N` (default: 1)

Runs N validate JVM subprocesses concurrently.  The existing
`validate_products()` function in `process_uploads.py` is wrapped in a
`ThreadPoolExecutor`; each batch runs its own validate subprocess so the GIL
is not a bottleneck.  Log filenames include a zero-padded batch index
(`_b0001.json`) to prevent concurrent write collisions.

### `--funpack-workers W` (default: 1)

Parallelises funpack/gzip decompression within a single batch.  Each worker
runs an independent subprocess via `ThreadPoolExecutor` in
`validation.validate_products()`.

### Benchmark results (sikhote, Java 17, 100 mixed products)

| Configuration | ms/product | Speedup |
|---|---|---|
| Baseline (1 batch, 1 funpack worker) | ~1,572 | 1.0× |
| 4 batches, 1 funpack worker | ~553 | 2.8× |
| 4 batches, 4 funpack workers | ~491 | 3.2× |
| 8 batches, 4 funpack workers | ~357 | 4.4× |

RAM: each JVM uses up to 4 GB heap.  4 parallel batches adds ~16 GB.
I/O: spinning-disk archives saturate around 8 parallel funpack streams.

Both flags default to 1, preserving exact original behaviour when omitted.
All tested configurations produce identical pass/fail outcomes to the
sequential baseline across 100+ products per run.

### Resource guidance

| parallel-batches | funpack-workers | Additional RAM | Use case |
|---|---|---|---|
| 1 | 1 | 0 | Original PSI behaviour |
| 4 | 4 | ~16 GB | Recommended for bulk backlog |
| 8 | 4 | ~32 GB | Maximum throughput, I/O limited |

Set `TMPDIR` to a large filesystem before running if `/tmp` is constrained.
Each parallel batch stages `batch_size × image_size` of decompressed data.

---

## Filter ValidateLauncher phantom entries from product counts

**File:** `ingest/validation.py`, `run_validator()`
**Commit:** `8c194a0`

### Root cause

`validate` inserts a `gov.nasa.pds.validate.ValidateLauncher` status=PASS entry
into `productLevelValidationResults` when a single batch contains products that
reference different PDS4 IM versions.  The entry carries a WARNING about multiple
IM versions detected in the run; it is not a real product result.

This fires once per full (100-product) batch that contains at least one product
using a non-dominant IM version.  For CSS data, `.tran_ai.xml` labels (G96 and
703) reference IM 1N00 (PDS4 v1.23.0.0) while all other product types reference
IM 1G00 (v1.16.0.0).  Because `.tran_ai` files are distributed uniformly through
the sorted label list, the phantom fires in every full batch for G96 and 703,
inflating their validated-product counts by 1 per full batch (e.g. +137 for G96
on a 138-batch night, +182 for 703).  Instruments with no `tran_ai` labels (I52,
V06, V00) are unaffected.

### Fix

Filter entries whose `label` field starts with `gov.nasa.pds.validate.` before
building the `failures`/`successes` lists:

```python
real_results = [x for x in result['productLevelValidationResults']
                if not x.get('label', '').startswith('gov.nasa.pds.validate.')]
failures  = [ValidationResult(x) for x in real_results if x['status'] == "FAIL"]
successes = [ValidationResult(x) for x in real_results if x['status'] == "PASS"]
```

File paths will never start with `gov.nasa.pds.validate.`, so no real product
result is ever filtered.

---

## Pending changes (not yet implemented)

- **Canary injection system:** `--canary-dir`, `--canaries-per-batch` flags to
  inject known-good and known-bad test articles into production batches as
  ongoing validation of the validator itself.

- **Per-type product count reporting:** break down PASS/FAIL counts by product
  type (arch, calb, sexb, tran_ai, etc.) in the validation summary log and report.
