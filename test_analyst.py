"""Offline regression checks for meanings as well as successful execution."""
import contextlib
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import akiya_growth_and_vacancy_analyst as app


class AnalystTests(unittest.TestCase):
    def fixture(self, rows):
        directory = tempfile.TemporaryDirectory(prefix="akiya-test-")
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "fixture.csv"
        headers = list(dict.fromkeys(key for row in rows for key in row))
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return str(path)

    def capture(self, function, *args, **kwargs):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            function(*args, **kwargs)
        return output.getvalue()

    def test_nonfinite_is_missing(self):
        for value in ["NaN", "inf", "-inf", ""]:
            self.assertIsNone(app.safe_float(value))
        self.assertEqual(app.safe_float("0"), 0)

    def test_ranking_excludes_aggregate_and_unknown_dwellings(self):
        rows = [dict(level=level, area_code=str(i), city_name="Test",
                     dwellings_total=dw, vacant_rate_pct="20")
                for i, (level, dw) in enumerate([
                    ("national", "99999"), ("prefecture", "9000"),
                    ("city", ""), ("city", "4999"), ("city", "5000")])]
        result = app.analyze_municipalities(self.fixture(rows))
        self.assertEqual([r["area_code"] for r in result], ["4"])

    def test_missing_selected_rate_is_not_zero(self):
        rows = [dict(level="city", city_name="Test", dwellings_total="5000",
                     vacant_rate_pct=rate) for rate in ["", "0", "NaN"]]
        result = app.analyze_municipalities(self.fixture(rows))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["vacant_rate_pct"], 0)
        self.assertIsNone(result[0]["vacant_for_sale"])

    def test_missing_optional_counts_render_without_fabrication(self):
        rows = [dict(level="city", city_name="Test", dwellings_total="5000",
                     vacant_rate_pct="10", vacant_other_rate_pct="3")]
        result = app.analyze_municipalities(self.fixture(rows))
        text = self.capture(app.print_municipalities_table, result, "vacant_rate_pct")
        self.assertIn("-", text)
        self.assertIsNone(result[0]["vacant_total"])

    def test_other_sort_headers_match_values(self):
        rows = app.analyze_municipalities(app.DEFAULT_MUNICIPALITIES,
                                         sort_key="vacant_other_rate_pct")
        text = self.capture(app.print_municipalities_table, rows,
                            "vacant_other_rate_pct", limit=1)
        headers = [part.strip() for part in text.splitlines()[0].split("|")]
        values = [part.strip() for part in text.splitlines()[2].split("|")]
        mapped = dict(zip(headers, values))
        self.assertEqual(mapped["空き家率(%)"], "21.30%")
        self.assertEqual(mapped["その他空き家率(%)"], "19.18%")

    def test_ward_is_not_labelled_prefecture(self):
        rows = app.analyze_municipalities(app.DEFAULT_MUNICIPALITIES)
        ward = next(row for row in rows if row["area_code"] == "01101")
        text = self.capture(app.print_municipalities_table, [ward], "vacant_rate_pct")
        self.assertIn("中央区", text)
        self.assertIn("01101", text)
        self.assertNotIn("県全体", text)

    def test_real_timeseries_dates_are_displayed(self):
        national = next(row for row in app.analyze_timeseries(app.DEFAULT_TIMESERIES)
                        if row["area_code"] == "00000")
        self.assertEqual((national["first_year"], national["last_year"]), (1973, 2023))
        text = self.capture(app.print_timeseries_table, [national])
        self.assertIn("1973", text)
        self.assertNotIn("1958/初期", text)

    def test_missing_timeseries_does_not_claim_zero_growth(self):
        rows = app.analyze_timeseries(self.fixture([
            {"area_name":"Missing", "vacant_total_2018":"", "vacant_total_2023":""}]))
        self.assertIsNone(rows[0]["cagr_pct"])
        self.assertIsNone(rows[0]["growth_pct"])
        self.assertIsNone(rows[0]["total_change"])

    def test_single_year_does_not_claim_growth(self):
        row = app.analyze_timeseries(self.fixture([
            {"area_name":"One", "vacant_total_2023":"100"}]))[0]
        self.assertIsNone(row["cagr_pct"])
        self.assertIsNone(row["growth_ratio"])

    def test_zero_endpoint_is_preserved(self):
        row = app.analyze_timeseries(self.fixture([
            {"area_name":"Zero", "vacant_total_2018":"100", "vacant_total_2023":"0"}]))[0]
        self.assertEqual(row["last_val"], 0)
        self.assertEqual(row["cagr_pct"], -100)
        self.assertEqual(row["total_change"], -100)

    def test_zero_start_has_no_percentage_but_has_difference(self):
        row = app.analyze_timeseries(self.fixture([
            {"area_name":"Zero", "vacant_total_2018":"0", "vacant_total_2023":"100"}]))[0]
        self.assertIsNone(row["cagr_pct"])
        self.assertIsNone(row["growth_pct"])
        self.assertEqual(row["total_change"], 100)

    def test_unknown_metric_does_not_silently_substitute(self):
        with self.assertRaises(ValueError):
            app.analyze_timeseries(app.DEFAULT_TIMESERIES, metric="misspelled")

    def test_cli_json_and_sample_scope(self):
        result = subprocess.run([sys.executable,"-B",app.__file__,"--format","json",
                                 "--limit","3"], text=True, capture_output=True, check=True)
        records = json.loads(result.stdout, parse_constant=lambda value: self.fail(value))
        self.assertEqual(len(records), 3)
        self.assertTrue(all(r["level"] in ("city", "ward") for r in records))
        self.assertIn("サンプル", result.stderr)
        self.assertIn("150", result.stderr)
        self.assertIn("143", result.stderr)
        self.assertIn("全国順位ではありません", result.stderr)


if __name__ == "__main__":
    unittest.main()
