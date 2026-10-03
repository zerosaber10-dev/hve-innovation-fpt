# Microsoft Teams App Packaging

This folder contains Microsoft Teams app package artifacts and packaging utilities for the Enterprise HR Time and Leave Copilot.

## Files

* [`manifest.json`](manifest.json): Teams app manifest conforming to Microsoft Teams schema v1.16.
* [`color.png`](color.png): 192x192 color PNG icon for the Teams store and application listing.
* [`outline.png`](outline.png): 32x32 transparent PNG icon for Teams navigation and headers.
* [`package.py`](package.py): Python packaging utility that validates schema compliance, checks icon dimensions, scans for zero secrets, and creates the distribution zip `hr-time-leave-teams.zip`.

## Usage

```bash
# Validate assets and create zip package
python package.py

# Re-generate icon assets
python package.py --generate-icons

# Validate without creating zip
python package.py --validate-only
```

For complete permissions documentation and sideloading instructions, refer to [`docs/deployment/azure-teams-deployment.md`](../../docs/deployment/azure-teams-deployment.md).
