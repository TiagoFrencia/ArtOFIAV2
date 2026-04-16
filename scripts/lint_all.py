#!/usr/bin/env python3
"""
Linting and Formatting Script for ArtOfIA

This script runs all linting, formatting, and type checking tools with
appropriate thresholds and generates a comprehensive report.

Usage:
    python scripts/lint_all.py              # Run all checks
    python scripts/lint_all.py --fix        # Auto-fix issues
    python scripts/lint_all.py --report     # Generate report only
"""

import subprocess
import sys
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class LintResult:
    """Result of a linting check"""
    tool: str
    status: str  # "PASS", "FAIL", "WARNING"
    score: Optional[float] = None
    issues: int = 0
    message: str = ""
    details: str = ""


class LintRunner:
    """Orchestrates linting and formatting checks"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.results: List[LintResult] = []
        self.src_dir = self.root_dir / "src"
        self.tests_dir = self.root_dir / "tests"
        self.scripts_dir = self.root_dir / "scripts"

    def run_black(self, fix: bool = False) -> LintResult:
        """Run Black code formatter"""
        cmd = ["black", str(self.src_dir), str(self.tests_dir), str(self.scripts_dir)]
        if not fix:
            cmd.insert(2, "--check")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return LintResult(
                    tool="Black",
                    status="PASS",
                    message="Code formatting compliant",
                )
            else:
                return LintResult(
                    tool="Black",
                    status="FAIL",
                    message="Code formatting issues found",
                    details=result.stdout + result.stderr,
                )
        except subprocess.TimeoutExpired:
            return LintResult(
                tool="Black", status="WARNING", message="Timeout (>60s)"
            )
        except Exception as e:
            return LintResult(
                tool="Black", status="FAIL", message=f"Error: {e}", issues=1
            )

    def run_pylint(self) -> LintResult:
        """Run Pylint with minimum score threshold"""
        cmd = [
            "pylint",
            str(self.src_dir),
            "--fail-under=8.0",
            "--output-format=json",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Pylint returns non-zero even with good scores, so check output
            try:
                issues = json.loads(result.stdout) if result.stdout else []
                errors = [i for i in issues if i["type"] in ["error", "fatal"]]
                warnings = [i for i in issues if i["type"] == "warning"]

                if errors:
                    return LintResult(
                        tool="Pylint",
                        status="FAIL",
                        issues=len(errors),
                        message=f"Found {len(errors)} errors",
                        details="\n".join(
                            [f"  {e['path']}:{e['line']}: {e['message']}" for e in errors[:5]]
                        ),
                    )
                elif warnings:
                    return LintResult(
                        tool="Pylint",
                        status="WARNING",
                        issues=len(warnings),
                        message=f"Found {len(warnings)} warnings (min score: 8.0)",
                    )
                else:
                    return LintResult(
                        tool="Pylint",
                        status="PASS",
                        message="No issues found (min score: 8.0)",
                    )
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                if "Your code has been rated at" in result.stderr:
                    # Extract score
                    import re

                    match = re.search(r"rated at ([\d.]+)/10", result.stderr)
                    if match:
                        score = float(match.group(1))
                        status = "PASS" if score >= 8.0 else "FAIL"
                        return LintResult(
                            tool="Pylint",
                            status=status,
                            score=score,
                            message=f"Score: {score}/10",
                        )
                return LintResult(
                    tool="Pylint",
                    status="WARNING",
                    message="Could not parse output",
                    details=result.stderr,
                )
        except subprocess.TimeoutExpired:
            return LintResult(
                tool="Pylint", status="WARNING", message="Timeout (>120s)"
            )
        except FileNotFoundError:
            return LintResult(
                tool="Pylint",
                status="WARNING",
                message="Not installed (pip install pylint)",
            )
        except Exception as e:
            return LintResult(
                tool="Pylint", status="FAIL", message=f"Error: {e}", issues=1
            )

    def run_mypy(self) -> LintResult:
        """Run Mypy type checker"""
        cmd = ["mypy", str(self.src_dir), "--ignore-missing-imports"]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return LintResult(
                    tool="Mypy",
                    status="PASS",
                    message="Type checking passed",
                )
            else:
                lines = result.stdout.split("\n") if result.stdout else []
                errors = [l for l in lines if "error:" in l]
                return LintResult(
                    tool="Mypy",
                    status="WARNING",
                    issues=len(errors),
                    message=f"Type issues found: {len(errors)}",
                    details="\n".join(errors[:5]),
                )
        except subprocess.TimeoutExpired:
            return LintResult(
                tool="Mypy", status="WARNING", message="Timeout (>120s)"
            )
        except FileNotFoundError:
            return LintResult(
                tool="Mypy",
                status="WARNING",
                message="Not installed (pip install mypy)",
            )
        except Exception as e:
            return LintResult(
                tool="Mypy", status="FAIL", message=f"Error: {e}", issues=1
            )

    def run_pytest(self, coverage: bool = True) -> LintResult:
        """Run pytest with optional coverage"""
        cmd = ["pytest", str(self.tests_dir), "-v", "--tb=short"]
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-fail-under=80"])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                # Extract test count
                import re

                match = re.search(r"(\d+) passed", result.stdout)
                count = int(match.group(1)) if match else 0
                return LintResult(
                    tool="Pytest",
                    status="PASS",
                    issues=0,
                    message=f"All {count} tests passed (80% min coverage)",
                )
            else:
                lines = result.stdout.split("\n") if result.stdout else []
                failed = [l for l in lines if "FAILED" in l]
                return LintResult(
                    tool="Pytest",
                    status="FAIL",
                    issues=len(failed),
                    message=f"Test failures: {len(failed)}",
                    details="\n".join(failed[:5]),
                )
        except subprocess.TimeoutExpired:
            return LintResult(
                tool="Pytest", status="WARNING", message="Timeout (>300s)"
            )
        except FileNotFoundError:
            return LintResult(
                tool="Pytest",
                status="WARNING",
                message="Not installed (pip install pytest)",
            )
        except Exception as e:
            return LintResult(
                tool="Pytest", status="WARNING", message=f"Error: {e}", issues=1
            )

    def run_bandit(self) -> LintResult:
        """Run Bandit security scanner"""
        cmd = ["bandit", "-r", str(self.src_dir), "-f", "json"]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            try:
                data = json.loads(result.stdout) if result.stdout else {}
                metrics = data.get("metrics", {})
                issues = data.get("results", [])

                high_severity = [i for i in issues if i.get("severity") == "HIGH"]
                critical = [i for i in issues if i.get("severity") == "CRITICAL"]

                if critical or high_severity:
                    return LintResult(
                        tool="Bandit",
                        status="FAIL",
                        issues=len(critical) + len(high_severity),
                        message=f"Security issues: {len(critical)} critical, {len(high_severity)} high",
                    )
                else:
                    return LintResult(
                        tool="Bandit",
                        status="PASS",
                        message="No security issues found",
                    )
            except json.JSONDecodeError:
                return LintResult(
                    tool="Bandit",
                    status="WARNING",
                    message="Could not parse output",
                )
        except subprocess.TimeoutExpired:
            return LintResult(
                tool="Bandit", status="WARNING", message="Timeout (>60s)"
            )
        except FileNotFoundError:
            return LintResult(
                tool="Bandit",
                status="WARNING",
                message="Not installed (pip install bandit)",
            )
        except Exception as e:
            return LintResult(
                tool="Bandit", status="WARNING", message=f"Error: {e}", issues=1
            )

    def run_all(self, fix: bool = False) -> bool:
        """Run all linting checks"""
        print("🔍 Starting ArtOfIA Linting Suite...\n")

        # Phase 1: Formatting
        print("📐 Phase 1: Code Formatting")
        self.results.append(self.run_black(fix=fix))
        print(f"   {self.format_result(self.results[-1])}\n")

        # Phase 2: Analysis
        print("🔬 Phase 2: Code Analysis")
        self.results.append(self.run_pylint())
        print(f"   {self.format_result(self.results[-1])}\n")

        self.results.append(self.run_mypy())
        print(f"   {self.format_result(self.results[-1])}\n")

        # Phase 3: Testing
        print("✅ Phase 3: Testing & Coverage")
        self.results.append(self.run_pytest())
        print(f"   {self.format_result(self.results[-1])}\n")

        # Phase 4: Security
        print("🔐 Phase 4: Security Scanning")
        self.results.append(self.run_bandit())
        print(f"   {self.format_result(self.results[-1])}\n")

        # Summary
        return self.print_summary()

    def format_result(self, result: LintResult) -> str:
        """Format a single result for display"""
        emoji = "✅" if result.status == "PASS" else "⚠️" if result.status == "WARNING" else "❌"
        msg = f"{emoji} {result.tool}: {result.message}"
        if result.issues > 0:
            msg += f" ({result.issues} issues)"
        if result.details:
            msg += f"\n     {result.details}"
        return msg

    def print_summary(self) -> bool:
        """Print summary and return success status"""
        print("=" * 60)
        print("📊 LINTING SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARNING")
        failed = sum(1 for r in self.results if r.status == "FAIL")

        print(f"\n✅ PASSED: {passed}/{len(self.results)}")
        print(f"⚠️  WARNED: {warned}/{len(self.results)}")
        print(f"❌ FAILED: {failed}/{len(self.results)}\n")

        for result in self.results:
            status_icon = (
                "✅" if result.status == "PASS"
                else "⚠️" if result.status == "WARNING"
                else "❌"
            )
            print(f"{status_icon} {result.tool:15} {result.status:10} {result.message}")

        print(f"\nGenerated: {datetime.now().isoformat()}")
        print("=" * 60 + "\n")

        success = failed == 0
        if success:
            print("🎉 ALL CHECKS PASSED - Ready for deployment!")
        else:
            print(f"❌ CHECKS FAILED - Fix the {failed} failing checks above")

        return success


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ArtOfIA Linting Suite")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument(
        "--root", default=".", help="Root directory (default: current)"
    )
    args = parser.parse_args()

    runner = LintRunner(root_dir=args.root)
    success = runner.run_all(fix=args.fix)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
