"""TRADEMARK specialist — public interface.

Owns trademarks.duckdb. Two data sources:
  - CSV bulk load (build.py): case_file and companion tables
  - TSDR API (enrich.py): mark_images and mark_case_status
"""

from markery.specialist.trademark.build import build, open_db
from markery.specialist.trademark.tsdr_client import TSDRClient
from markery.specialist.trademark.enrich import store_mark_image, store_case_status

__all__ = [
    "build",
    "open_db",
    "TSDRClient",
    "store_mark_image",
    "store_case_status",
]
