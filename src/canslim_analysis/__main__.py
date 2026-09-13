"""Allow the pipeline to be run with ``python -m canslim_analysis``."""

from __future__ import annotations

from canslim_analysis.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
