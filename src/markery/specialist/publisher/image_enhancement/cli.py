"""
CLI entry point for image_tools.

Usage:
  python -m image_tools enhance <serial_no> --out-dir output/enhanced_foo
  python -m image_tools batch "filing_dt BETWEEN DATE '1930-05-01' AND DATE '1930-05-31' AND mark_draw_cd LIKE '3%'" --out-dir output/enhanced_may1930
  python -m image_tools gallery output/enhanced_may1930 --title "Design Marks, May 1930"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

from .gallery import build_gallery


def _result_line(result) -> str:
    svg = " + SVG" if result.svg_path else ""
    return f"  OK  {result.serial_no}{svg}  ({result.model_used})"


def cmd_enhance(args) -> None:
    from .pipeline import process_mark
    result = process_mark(
        args.serial_no,
        input_path=Path(args.input_path) if args.input_path else None,
        out_dir=Path(args.out_dir),
        db_path=args.db,
        force=args.force,
    )
    print(_result_line(result))


def cmd_print(args) -> None:
    import sys
    from .print_asset import build_print_asset, SPECS
    spec = SPECS.get(args.spec)
    try:
        out = build_print_asset(
            args.ident, args.project, kind=args.kind, spec_name=args.spec,
            upscale_first=not args.no_upscale,
        )
    except PermissionError as e:
        print(f"  SKIP  {e}", file=sys.stderr)
        sys.exit(1)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR  {e}", file=sys.stderr)
        sys.exit(1)
    dims = f"{spec['w']}x{spec['h']}@{spec['dpi']}dpi" if spec else args.spec
    print(f"  OK  {args.ident}  →  {out}  ({dims}, {out.stat().st_size // 1024} KB)")


def cmd_batch(args) -> None:
    from .pipeline import process_mark
    conn = duckdb.connect(args.db, read_only=True)
    rows = conn.execute(f"""
        SELECT
            cf.serial_no::VARCHAR,
            cf.mark_draw_cd,
            COALESCE(
                (SELECT LIST(design_search_cd) FROM design_search
                 WHERE serial_no = cf.serial_no),
                []
            ) AS ds_codes
        FROM case_file cf
        WHERE {args.where}
        ORDER BY cf.serial_no
    """).fetchall()
    conn.close()

    out_dir = Path(args.out_dir)
    ok = 0
    for sn, draw_cd, ds_codes in rows:
        try:
            result = process_mark(
                sn,
                out_dir=out_dir,
                db_path=args.db,
                design_codes=ds_codes or [],
                draw_cd=draw_cd or "3000",
                force=args.force,
            )
            print(_result_line(result))
            ok += 1
        except Exception as exc:
            print(f"  ERR {sn}: {exc}", file=sys.stderr)

    print(f"\n{ok}/{len(rows)} processed → {out_dir}")


def cmd_gallery(args) -> None:
    import duckdb as _duckdb

    if args.img_dir:
        # Directory mode: build from enhanced PNGs
        img_dir = Path(args.img_dir)
        serial_nos = [p.stem for p in sorted(img_dir.glob("*.png"))]
        if not serial_nos:
            print(f"No PNG files found in {img_dir}", file=sys.stderr)
            sys.exit(1)
        out_path = Path(args.out) if args.out else img_dir / "gallery.html"
        build_gallery(
            serial_nos,
            out_path=out_path,
            img_dir=img_dir,
            title=args.title,
            subtitle=args.subtitle,
            db_path=args.db,
        )
    elif args.where:
        # DB mode: build from mark_images table, no enhancement needed
        if not args.out:
            print("--out is required with --where", file=sys.stderr)
            sys.exit(1)
        conn = _duckdb.connect(args.db, read_only=True)
        rows = conn.execute(f"""
            SELECT cf.serial_no::VARCHAR
            FROM case_file cf
            WHERE {args.where}
            ORDER BY cf.filing_dt, cf.serial_no
        """).fetchall()
        conn.close()
        serial_nos = [r[0] for r in rows]
        if not serial_nos:
            print("No marks matched the WHERE clause", file=sys.stderr)
            sys.exit(1)
        build_gallery(
            serial_nos,
            out_path=Path(args.out),
            img_dir=None,
            title=args.title,
            subtitle=args.subtitle,
            db_path=args.db,
        )
        print(f"Gallery → {args.out}  ({len(serial_nos)} cards)")
    else:
        print("Provide img_dir (enhanced PNGs) or --where (DB images)", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    from markery.common.config import DB
    parser = argparse.ArgumentParser(prog="image_enhancement")
    parser.add_argument("--db", default=str(DB["trademarks"]), help="Path to trademarks.duckdb")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enhance = sub.add_parser("enhance", help="Enhance a single mark by serial number")
    p_enhance.add_argument("serial_no")
    p_enhance.add_argument("--input-path", default=None, help="Source PNG file (overrides DB lookup)")
    p_enhance.add_argument("--out-dir", default="output/enhanced", required=False)
    p_enhance.add_argument("--force", action="store_true", help="Re-process even if output exists")

    p_batch = sub.add_parser("batch", help="Enhance all marks matching a SQL WHERE clause")
    p_batch.add_argument(
        "where",
        help="SQL WHERE clause applied to case_file (aliased cf). "
             "Example: \"filing_dt BETWEEN DATE '1930-05-01' AND DATE '1930-05-31'\"",
    )
    p_batch.add_argument("--out-dir", required=True, help="Output directory for PNGs and SVGs")
    p_batch.add_argument("--force", action="store_true")

    p_gallery = sub.add_parser(
        "gallery",
        help="Build an HTML gallery — from enhanced PNGs (img_dir) or raw DB images (--where)",
    )
    p_gallery.add_argument(
        "img_dir", nargs="?",
        help="Directory of enhanced PNGs. Omit and use --where to build from DB images instead.",
    )
    p_gallery.add_argument(
        "--where",
        help="SQL WHERE clause on case_file to select marks; reads images from mark_images table",
    )
    p_gallery.add_argument(
        "--out",
        help="Output path for gallery.html. Defaults to <img_dir>/gallery.html in directory mode.",
    )
    p_gallery.add_argument("--title", default="Trademark Marks")
    p_gallery.add_argument("--subtitle", default="")

    p_print = sub.add_parser(
        "print",
        help="Build a print-ready PNG for on-demand printing (Amazon Merch) "
             "from an eligible PD source → projects/<project>/print/",
    )
    p_print.add_argument("ident", help="Trademark serial number or patent number (e.g. US1525813A)")
    p_print.add_argument("--project", required=True, help="Target project (output → projects/<p>/print/)")
    p_print.add_argument("--kind", choices=["mark", "patent"], default=None,
                         help="Source kind (auto-detected from the identifier if omitted)")
    p_print.add_argument("--spec", default="merch", help="Print spec (default: merch)")
    p_print.add_argument("--no-upscale", action="store_true",
                         help="Skip the upscale step (faster; lower print resolution)")

    args = parser.parse_args()
    {"enhance": cmd_enhance, "batch": cmd_batch, "gallery": cmd_gallery,
     "print": cmd_print}[args.cmd](args)
