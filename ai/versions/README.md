# Dataset Versions

Dataset versions are immutable once used for training.

Each version folder should contain:

- `manifest.json`
- `split_summary.json`
- `validation_report.json`
- `export_manifest.json`
- `augmentation_profile.yaml`

Version naming:

```text
v<major>.<minor>.<patch>
```

Examples:

- `v0.1.0`: first annotated pothole foundation dataset
- `v0.2.0`: adds negative samples and rainy road coverage
- `v1.0.0`: first production candidate dataset
