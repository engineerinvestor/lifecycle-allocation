"""Tests for CLI."""

import json
import os
import tempfile

from click.testing import CliRunner

from lifecycle_allocation.cli.main import cli


class TestCLI:
    def test_alloc_produces_output_files(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "alloc",
                    "--profile",
                    "examples/profiles/young_saver.yaml",
                    "--out",
                    tmpdir,
                ],
            )
            assert result.exit_code == 0, result.output
            assert os.path.exists(os.path.join(tmpdir, "allocation.json"))
            assert os.path.exists(os.path.join(tmpdir, "summary.md"))

    def test_alloc_with_report(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "alloc",
                    "--profile",
                    "examples/profiles/young_saver.yaml",
                    "--out",
                    tmpdir,
                    "--report",
                ],
            )
            assert result.exit_code == 0, result.output
            charts_dir = os.path.join(tmpdir, "charts")
            assert os.path.exists(os.path.join(charts_dir, "balance_sheet.png"))
            assert os.path.exists(os.path.join(charts_dir, "strategy_bars.png"))

    def test_alloc_json_valid(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "alloc",
                    "--profile",
                    "examples/profiles/mid_career.yaml",
                    "--out",
                    tmpdir,
                ],
            )
            assert result.exit_code == 0
            with open(os.path.join(tmpdir, "allocation.json")) as f:
                data = json.load(f)
            assert "alpha_recommended" in data
            assert 0 <= data["alpha_recommended"] <= 2.0

    def test_cli_flag_overrides(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "alloc",
                    "--profile",
                    "examples/profiles/young_saver.yaml",
                    "--out",
                    tmpdir,
                    "--mu",
                    "0.07",
                    "--sigma",
                    "0.20",
                ],
            )
            assert result.exit_code == 0

    def test_leverage_flags(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "alloc",
                    "--profile",
                    "examples/profiles/young_saver.yaml",
                    "--out",
                    tmpdir,
                    "--allow-leverage",
                    "--max-leverage",
                    "1.5",
                    "--borrowing-spread",
                    "0.015",
                ],
            )
            assert result.exit_code == 0

    def test_svg_format(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "alloc",
                    "--profile",
                    "examples/profiles/young_saver.yaml",
                    "--out",
                    tmpdir,
                    "--report",
                    "--format",
                    "svg",
                ],
            )
            assert result.exit_code == 0
            charts_dir = os.path.join(tmpdir, "charts")
            assert os.path.exists(os.path.join(charts_dir, "balance_sheet.svg"))
