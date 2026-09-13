# Configuration

Configuration is supplied by validated CLI options, not source constants.

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
