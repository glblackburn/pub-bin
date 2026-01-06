# Trufflehog Scripts - Defect Tracking

This section tracks known bugs and issues in the trufflehog scripts.

| ID | Status | Priority | Severity | Title | Description |
|----|--------|----------|----------|-------|-------------|
| [BUG-1](BUG-1.md) | Fixed | High | Medium | Script Prompts for Key Before Validating Prerequisites | Script prompts for sensitive AWS key input before validating that report file exists and identifier is valid, causing unnecessary secret entry when script will fail immediately |

## Legend

- **Status:** Fixed, Open, In Progress, Closed, Not Fixable
- **Priority:** Low, Medium, High, Critical
- **Severity:** Low, Medium, High, Critical

## Feature and Defect Tree

See [FEATURE_DEFECT_TREE.md](FEATURE_DEFECT_TREE.md) for a comprehensive tree structure of all features and defects.
