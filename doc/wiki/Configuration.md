# Configuration

Configuration is supplied through validated CLI options. Code defaults exist only as documented fallbacks; operators do not edit source constants or generated JSON to change a run.

Run `python -m canslim_analysis quantitative --help` for the current list. Important defaults are:

| Option group | Default |
|---|---|
| Quarterly and annual EPS growth | `0.25` |
| Minimum RS rating | `80.0` |
| Strong-volume ratio | `1.5` |
| Positive volume skew | `1.2` |
| Institutional ownership reference | `0.30` |
| Near-high threshold | `0.10` |
| Workers | `5` |
| Request timeout | `10` seconds |
| Retries | `3` |
| Retry delay | `2` seconds |

The output directory defaults to `out/` and can be overridden with `--output-dir`. No workflow requires editing generated JSON.

Run `python -m canslim_analysis run --help` for orchestration options. The complete default inventory and evidence sources are in [artifact inventory](artifact-inventory.md); operational boundaries are in [operations](operations.md).
