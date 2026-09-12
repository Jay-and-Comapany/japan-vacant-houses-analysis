#!/usr/bin/env python3
"""akiya_growth_and_vacancy_analyst.py — Japan Vacant Houses & Housing Statistics Analyzer.

Analyzes 65-year longitudinal trends (1958-2023) and municipality-level vacancy rates
from official Statistics Bureau Housing and Land Survey (住宅・土地統計調査) data.

Standard library only. No external dependencies required.
"""
import sys
import os
import csv
import math
import json
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TIMESERIES = os.path.join(SCRIPT_DIR, "sample_timeseries_wide_1958-2023.csv")
DEFAULT_MUNICIPALITIES = os.path.join(SCRIPT_DIR, "sample_municipalities_r05_2023.csv")


def safe_float(v, default=None):
    if v is None:
        return default
    v_str = str(v).strip().replace(",", "")
    if not v_str:
        return default
    try:
        return float(v_str)
    except ValueError:
        return default


def safe_int(v, default=None):
    f = safe_float(v, default)
    return int(f) if f is not None else default


def analyze_timeseries(filepath, target_pref=None, metric="vacant_total"):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Timeseries CSV not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Find columns matching {metric}_YYYY
    prefix = f"{metric}_"
    metric_cols = [c for c in reader.fieldnames if c.startswith(prefix) and c[len(prefix):].isdigit()]
    if not metric_cols:
        # Fallback to any vacant_total_YYYY
        prefix = "vacant_total_"
        metric_cols = [c for c in reader.fieldnames if c.startswith(prefix) and c[len(prefix):].isdigit()]

    metric_cols.sort(key=lambda c: int(c[len(prefix):]))

    results = []
    for r in rows:
        area_name = r.get("area_name", "") or r.get("pref_name", "")
        if not area_name:
            continue
        if target_pref and target_pref not in area_name:
            continue

        first_year = None
        last_year = None
        first_val = None
        last_val = None

        history = []
        for col in metric_cols:
            y = int(col[len(prefix):])
            val = safe_float(r.get(col))
            if val is not None and val > 0:
                history.append((y, val))
                if first_year is None:
                    first_year = y
                    first_val = val
                last_year = y
                last_val = val

        if first_year and last_year and first_year != last_year and first_val and first_val > 0:
            years_diff = last_year - first_year
            ratio = last_val / first_val
            cagr = (math.pow(ratio, 1.0 / years_diff) - 1.0) * 100.0
            total_change = last_val - first_val
            growth_pct = (ratio - 1.0) * 100.0
        else:
            cagr = 0.0
            growth_pct = 0.0
            total_change = 0.0

        results.append({
            "area_name": area_name,
            "area_code": r.get("area_code", ""),
            "level": r.get("level", ""),
            "metric": prefix.rstrip("_"),
            "first_year": first_year,
            "first_val": first_val,
            "last_year": last_year,
            "last_val": last_val,
            "growth_ratio": round(last_val / first_val, 2) if (first_val and first_val > 0) else None,
            "growth_pct": round(growth_pct, 1),
            "cagr_pct": round(cagr, 2),
            "total_change": round(total_change, 1),
            "history": history,
        })

    return results


def analyze_municipalities(filepath, min_dwellings=5000, sort_key="vacant_rate_pct", reverse=True):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Municipalities CSV not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    records = []
    for r in rows:
        dwellings = safe_int(r.get("dwellings_total"))
        if dwellings is not None and dwellings < min_dwellings:
            continue

        v_total = safe_int(r.get("vacant_total"), 0)
        v_rate = safe_float(r.get("vacant_rate_pct"), 0.0)
        v_other = safe_int(r.get("vacant_other"), 0)
        v_other_rate = safe_float(r.get("vacant_other_rate_pct"), 0.0)
        v_rent = safe_int(r.get("vacant_for_rent"), 0)
        v_sale = safe_int(r.get("vacant_for_sale"), 0)
        v_sec = safe_int(r.get("vacant_secondary"), 0)

        records.append({
            "area_code": r.get("area_code", ""),
            "pref_name": r.get("pref_name", ""),
            "city_name": r.get("city_name", ""),
            "level": r.get("level", ""),
            "dwellings_total": dwellings,
            "vacant_total": v_total,
            "vacant_rate_pct": v_rate,
            "vacant_other": v_other,
            "vacant_other_rate_pct": v_other_rate,
            "vacant_for_rent": v_rent,
            "vacant_for_sale": v_sale,
            "vacant_secondary": v_sec,
        })

    records.sort(key=lambda x: (x.get(sort_key) is not None, x.get(sort_key)), reverse=reverse)
    return records


def print_timeseries_table(results, limit=20):
    print(f"{'地域 / 都道府県':<12} | {'指標':<12} | {'1958/初期':>12} | {'2023最新':>12} | {'倍率':>8} | {'全成長率':>10} | {'CAGR(年平均)':>12}")
    print("-" * 84)
    for r in results[:limit]:
        f_val_str = f"{r['first_val']:,}" if r['first_val'] is not None else "-"
        l_val_str = f"{r['last_val']:,}" if r['last_val'] is not None else "-"
        ratio_str = f"{r['growth_ratio']}x" if r['growth_ratio'] is not None else "-"
        growth_str = f"+{r['growth_pct']}%" if r['growth_pct'] > 0 else f"{r['growth_pct']}%"
        cagr_str = f"+{r['cagr_pct']}%/yr" if r['cagr_pct'] > 0 else f"{r['cagr_pct']}%/yr"
        print(f"{r['area_name']:<12} | {r['metric']:<12} | {f_val_str:>12} | {l_val_str:>12} | {ratio_str:>8} | {growth_str:>10} | {cagr_str:>12}")


def print_municipalities_table(records, sort_key, limit=20):
    header_name = "空き家率(%)" if sort_key == "vacant_rate_pct" else "放置空き家率(%)"
    print(f"{'順位':<4} | {'都道府県':<8} | {'市区町村':<14} | {'総住宅数':>10} | {'空き家総数':>10} | {header_name:>12} | {'放置空き家':>10} | {'放置率(%)':>10}")
    print("-" * 96)
    for idx, r in enumerate(records[:limit], 1):
        d_str = f"{r['dwellings_total']:,}" if r['dwellings_total'] is not None else "-"
        v_str = f"{r['vacant_total']:,}"
        vr_str = f"{r['vacant_rate_pct']:.2f}%"
        vo_str = f"{r['vacant_other']:,}"
        vor_str = f"{r['vacant_other_rate_pct']:.2f}%"
        city_display = r['city_name'] if r['city_name'] else "(県全体)"
        print(f"{idx:<4} | {r['pref_name']:<8} | {city_display:<14} | {d_str:>10} | {v_str:>10} | {vr_str:>12} | {vo_str:>10} | {vor_str:>10}")


def main():
    parser = argparse.ArgumentParser(
        description="Japan Vacant Houses & Housing Statistics 65-Year Analyzer (1958-2023)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 akiya_growth_and_vacancy_analyst.py --mode timeseries
  python3 akiya_growth_and_vacancy_analyst.py --mode ranking --sort other --limit 15
  python3 akiya_growth_and_vacancy_analyst.py --mode ranking --min-dwellings 20000 --limit 10
  python3 akiya_growth_and_vacancy_analyst.py --format json --limit 5
"""
    )
    parser.add_argument("--mode", choices=["timeseries", "ranking"], default="ranking",
                        help="Analysis mode: 'timeseries' (65-year longitudinal CAGR) or 'ranking' (municipality rankings)")
    parser.add_argument("--timeseries-csv", default=DEFAULT_TIMESERIES,
                        help="Path to timeseries wide CSV file")
    parser.add_argument("--muni-csv", default=DEFAULT_MUNICIPALITIES,
                        help="Path to municipality details CSV file")
    parser.add_argument("--sort", choices=["total", "other"], default="total",
                        help="Sorting metric: 'total' for vacant_rate_pct, 'other' for vacant_other_rate_pct (放置空き家)")
    parser.add_argument("--min-dwellings", type=int, default=5000,
                        help="Filter out small municipalities with fewer than N total dwellings (default: 5000)")
    parser.add_argument("--pref", default=None,
                        help="Filter timeseries by prefecture name")
    parser.add_argument("--limit", type=int, default=20,
                        help="Number of records to display (default: 20)")
    parser.add_argument("--format", choices=["table", "json"], default="table",
                        help="Output format (default: table)")

    args = parser.parse_args()

    if args.mode == "timeseries":
        results = analyze_timeseries(args.timeseries_csv, target_pref=args.pref)
        if args.format == "json":
            print(json.dumps(results[:args.limit], ensure_ascii=False, indent=2))
        else:
            print(f"\n=== 日本全国・都道府県別 空き家65年間推移・CAGR成長分析 (1958〜2023年) ===\n")
            print_timeseries_table(results, limit=args.limit)
            print(f"\n※ 出典: 総務省統計局「住宅・土地統計調査」（昭和33年〜令和5年）")
            print(f"※ 商用データカタログ: https://jay-portal.pages.dev/catalog/#akiya\n")
    else:
        sort_col = "vacant_other_rate_pct" if args.sort == "other" else "vacant_rate_pct"
        records = analyze_municipalities(args.muni_csv, min_dwellings=args.min_dwellings, sort_key=sort_col, reverse=True)
        if args.format == "json":
            print(json.dumps(records[:args.limit], ensure_ascii=False, indent=2))
        else:
            sort_desc = "放置空き家率（その他の空き家率）" if args.sort == "other" else "空き家総率"
            print(f"\n=== 令和5年(2023年) 市区町村別 {sort_desc} 上位ランキング (総住宅数 {args.min_dwellings:,}戸以上) ===\n")
            print_municipalities_table(records, sort_key=sort_col, limit=args.limit)
            print(f"\n※ 出典: 総務省統計局「令和5年住宅・土地統計調査」公表データ")
            print(f"※ 商用データカタログ: https://jay-portal.pages.dev/catalog/#akiya\n")


if __name__ == "__main__":
    main()
