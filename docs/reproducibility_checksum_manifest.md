# Reproducibility Checksum Manifest

Generated: 2026-08-02T01:41:05

Purpose:

```text
Record SHA256 hashes and file sizes for the stable reproducibility package artifacts.
Dynamic build reports and self-referential audit outputs are excluded to avoid circular hashes.
```

## Summary

```text
artifacts_hashed = 184
checkpoint = 10
documentation = 39
environment_adapter = 3
figure = 19
latex = 13
result = 50
script = 50
```

## Size by Group

| Group | Files | Size MB |
|---|---:|---:|
| checkpoint | 10 | 2.926 |
| documentation | 39 | 0.227 |
| environment_adapter | 3 | 0.062 |
| figure | 19 | 1.675 |
| latex | 13 | 0.054 |
| result | 50 | 0.239 |
| script | 50 | 0.423 |

## Excluded Dynamic Artifacts

```text
docs/paper_asset_build_report.md
docs/reproducibility_checksum_manifest.md
docs/reproducibility_checksum_verification.md
docs/result_provenance_audit.md
docs/supplemental_csv_schema_audit.md
docs/supplemental_data_readme.md
results/reproducibility_checksum_manifest.csv
results/reproducibility_checksum_verification.csv
results/result_provenance_audit.csv
results/supplemental_csv_schema_audit.csv
```

## Use Boundary

```text
Use this manifest after packaging or moving the project to verify that stable artifacts are unchanged.
Regenerate it after rerunning experiments, changing manuscript text, or updating figures/tables.
```
