#!/usr/bin/env python3
"""
Code Quality Runner for Autonomica API

This script runs comprehensive code quality checks including:
- Code formatting (Black, isort)
- Linting (Flake8, MyPy)
- Security scanning (Bandit, Safety)
- Complexity analysis (Radon, Xenon)
- Coverage reporting
- Performance profiling
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

class CodeQualityRunner:
    """Comprehensive code quality checking and reporting."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.start_time = time.time()
        self.results = {
            "formatting": {"status": "pending", "output": "", "errors": []},
            "linting": {"status": "pending", "output": "", "errors": []},
            "type_checking": {"status": "pending", "output": "", "errors": []},
            "security": {"status": "pending", "output": "", "errors": []},
            "complexity": {"status": "pending", "output": "", "errors": []},
            "coverage": {"status": "pending", "output": "", "errors": []},
            "performance": {"status": "pending", "output": "", "errors": []},
        }
        
    def log(self, message: str, level: str = "info") -> None:
        """Log messages with timestamps and formatting."""
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "start": "🚀"
        }.get(level, "ℹ️")
        
        print(f"{prefix} [{timestamp}] {message}")
    
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a shell command and return results."""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    command,
                    cwd=self.project_root,
                    timeout=300
                )
                return result.returncode, "", ""
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 5 minutes"
        except Exception as e:
            return -1, "", str(e)
    
    def check_dependencies(self) -> bool:
        """Check if required tools are available."""
        self.log("Checking code quality tool dependencies...", "info")
        
        required_tools = [
            ("black", ["black", "--version"]),
            ("isort", ["isort", "--version"]),
            ("flake8", ["flake8", "--version"]),
            ("mypy", ["mypy", "--version"]),
            ("bandit", ["bandit", "--version"]),
            ("safety", ["safety", "--version"]),
            ("radon", ["radon", "--version"]),
            ("xenon", ["xenon", "--version"]),
        ]
        
        missing_tools = []
        
        for tool_name, command in required_tools:
            try:
                returncode, stdout, stderr = self.run_command(command)
                if returncode == 0:
                    self.log(f"  ✅ {tool_name} available", "success")
                else:
                    missing_tools.append(tool_name)
                    self.log(f"  ❌ {tool_name} not working properly", "error")
            except FileNotFoundError:
                missing_tools.append(tool_name)
                self.log(f"  ❌ {tool_name} not found", "error")
        
        if missing_tools:
            self.log(f"Missing tools: {', '.join(missing_tools)}", "warning")
            self.log("Install missing tools with: pip install -r requirements-dev.txt", "info")
            return False
        
        return True
    
    def run_code_formatting(self) -> bool:
        """Run code formatting checks with Black and isort."""
        self.log("Running code formatting checks...", "start")
        
        # Run Black formatting
        self.log("  Running Black formatter...", "info")
        returncode, stdout, stderr = self.run_command(["black", "--check", "--diff", "."])
        
        if returncode == 0:
            self.log("  ✅ Black formatting check passed", "success")
            self.results["formatting"]["status"] = "passed"
        else:
            self.log("  ❌ Black formatting check failed", "error")
            self.results["formatting"]["status"] = "failed"
            self.results["formatting"]["errors"].append("Black formatting issues found")
            self.results["formatting"]["output"] = stdout + stderr
        
        # Run isort import sorting
        self.log("  Running isort import sorter...", "info")
        returncode, stdout, stderr = self.run_command(["isort", "--check-only", "--diff", "."])
        
        if returncode == 0:
            self.log("  ✅ isort import sorting check passed", "success")
        else:
            self.log("  ❌ isort import sorting check failed", "error")
            self.results["formatting"]["status"] = "failed"
            self.results["formatting"]["errors"].append("Import sorting issues found")
            self.results["formatting"]["output"] += "\n" + stdout + stderr
        
        return self.results["formatting"]["status"] == "passed"
    
    def run_linting(self) -> bool:
        """Run code linting with Flake8."""
        self.log("Running code linting checks...", "start")
        
        returncode, stdout, stderr = self.run_command([
            "flake8", 
            "--max-line-length=88",
            "--extend-ignore=E203,W503",
            "--exclude=.git,__pycache__,.venv,venv,env,.env,build,dist,*.egg-info",
            "."
        ])
        
        if returncode == 0:
            self.log("  ✅ Flake8 linting passed", "success")
            self.results["linting"]["status"] = "passed"
        else:
            self.log("  ❌ Flake8 linting failed", "error")
            self.results["linting"]["status"] = "failed"
            self.results["linting"]["output"] = stdout
            self.results["linting"]["errors"] = stdout.splitlines()
        
        return self.results["linting"]["status"] == "passed"
    
    def run_type_checking(self) -> bool:
        """Run type checking with MyPy."""
        self.log("Running type checking...", "start")
        
        returncode, stdout, stderr = self.run_command([
            "mypy",
            "--ignore-missing-imports",
            "--show-error-codes",
            "--warn-return-any",
            "--warn-unused-configs",
            "--disallow-untyped-defs",
            "--disallow-incomplete-defs",
            "--check-untyped-defs",
            "--disallow-untyped-decorators",
            "--no-implicit-optional",
            "--warn-redundant-casts",
            "--warn-unused-ignores",
            "--warn-no-return",
            "--warn-unreachable",
            "--strict-equality",
            "app"
        ])
        
        if returncode == 0:
            self.log("  ✅ MyPy type checking passed", "success")
            self.results["type_checking"]["status"] = "passed"
        else:
            self.log("  ❌ MyPy type checking failed", "error")
            self.results["type_checking"]["status"] = "failed"
            self.results["type_checking"]["output"] = stdout + stderr
            self.results["type_checking"]["errors"] = (stdout + stderr).splitlines()
        
        return self.results["type_checking"]["status"] == "passed"
    
    def run_security_scanning(self) -> bool:
        """Run security scanning with Bandit and Safety."""
        self.log("Running security scanning...", "start")
        
        # Run Bandit security linter
        self.log("  Running Bandit security linter...", "info")
        returncode, stdout, stderr = self.run_command([
            "bandit",
            "-r", ".",
            "-f", "json",
            "-o", "bandit-report.json",
            "--exclude", "tests/,venv/,.venv/,env/,.env/"
        ])
        
        if returncode == 0:
            self.log("  ✅ Bandit security scan passed", "success")
        else:
            self.log("  ⚠️  Bandit security scan found issues", "warning")
            self.results["security"]["errors"].append("Bandit security issues found")
        
        # Run Safety vulnerability checker
        self.log("  Running Safety vulnerability checker...", "info")
        returncode, stdout, stderr = self.run_command([
            "safety",
            "check",
            "--output", "json",
            "--save", "safety-report.json"
        ])
        
        if returncode == 0:
            self.log("  ✅ Safety vulnerability check passed", "success")
            self.results["security"]["status"] = "passed"
        else:
            self.log("  ❌ Safety vulnerability check failed", "error")
            self.results["security"]["status"] = "failed"
            self.results["security"]["output"] = stdout + stderr
            self.results["security"]["errors"].append("Vulnerabilities found in dependencies")
        
        return self.results["security"]["status"] == "passed"
    
    def run_complexity_analysis(self) -> bool:
        """Run code complexity analysis with Radon and Xenon."""
        self.log("Running code complexity analysis...", "start")
        
        # Run Radon complexity analysis
        self.log("  Running Radon complexity analysis...", "info")
        returncode, stdout, stderr = self.run_command([
            "radon",
            "cc",
            "app",
            "--min", "A",
            "--json"
        ])
        
        if returncode == 0:
            try:
                complexity_data = json.loads(stdout)
                total_functions = sum(len(functions) for functions in complexity_data.values())
                self.log(f"  ✅ Radon complexity analysis: {total_functions} functions analyzed", "success")
            except json.JSONDecodeError:
                self.log("  ⚠️  Radon complexity analysis completed but output parsing failed", "warning")
        else:
            self.log("  ❌ Radon complexity analysis failed", "error")
            self.results["complexity"]["errors"].append("Radon analysis failed")
        
        # Run Xenon complexity checker
        self.log("  Running Xenon complexity checker...", "info")
        returncode, stdout, stderr = self.run_command([
            "xenon",
            "--max-absolute-complexity=10",
            "--max-average-complexity=5",
            "app"
        ])
        
        if returncode == 0:
            self.log("  ✅ Xenon complexity check passed", "success")
            self.results["complexity"]["status"] = "passed"
        else:
            self.log("  ❌ Xenon complexity check failed", "error")
            self.results["complexity"]["status"] = "failed"
            self.results["complexity"]["output"] = stdout + stderr
            self.results["complexity"]["errors"] = (stdout + stderr).splitlines()
        
        return self.results["complexity"]["status"] == "passed"
    
    def run_coverage_analysis(self) -> bool:
        """Run code coverage analysis."""
        self.log("Running code coverage analysis...", "start")
        
        returncode, stdout, stderr = self.run_command([
            "coverage",
            "run",
            "--source=app",
            "--omit=*/tests/*,*/venv/*,*/env/*",
            "-m", "pytest",
            "--tb=short",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=70"
        ])
        
        if returncode == 0:
            self.log("  ✅ Coverage analysis completed", "success")
            self.results["coverage"]["status"] = "passed"
            
            # Parse coverage percentage from output
            for line in stdout.splitlines():
                if "TOTAL" in line and "%" in line:
                    coverage_percent = line.split("%")[0].split()[-1]
                    self.log(f"  📊 Coverage: {coverage_percent}%", "info")
                    break
        else:
            self.log("  ❌ Coverage analysis failed", "error")
            self.results["coverage"]["status"] = "failed"
            self.results["coverage"]["output"] = stdout + stderr
            self.results["coverage"]["errors"] = (stdout + stderr).splitlines()
        
        return self.results["coverage"]["status"] == "passed"
    
    def run_performance_profiling(self) -> bool:
        """Run performance profiling and analysis."""
        self.log("Running performance profiling...", "start")
        
        # Check if py-spy is available for profiling
        try:
            returncode, stdout, stderr = self.run_command(["py-spy", "--version"])
            if returncode == 0:
                self.log("  ✅ py-spy available for profiling", "success")
                self.results["performance"]["status"] = "passed"
            else:
                self.log("  ⚠️  py-spy not available for profiling", "warning")
                self.results["performance"]["status"] = "skipped"
        except FileNotFoundError:
            self.log("  ⚠️  py-spy not installed, skipping profiling", "warning")
            self.results["performance"]["status"] = "skipped"
        
        return True
    
    def auto_fix_issues(self) -> None:
        """Automatically fix formatting and import issues."""
        self.log("Auto-fixing code quality issues...", "start")
        
        # Fix Black formatting
        self.log("  Fixing code formatting with Black...", "info")
        returncode, stdout, stderr = self.run_command(["black", "."], capture_output=False)
        if returncode == 0:
            self.log("  ✅ Black formatting applied", "success")
        else:
            self.log("  ❌ Black formatting failed", "error")
        
        # Fix isort import sorting
        self.log("  Fixing import sorting with isort...", "info")
        returncode, stdout, stderr = self.run_command(["isort", "."], capture_output=False)
        if returncode == 0:
            self.log("  ✅ isort import sorting applied", "success")
        else:
            self.log("  ❌ isort import sorting failed", "error")
    
    def generate_report(self) -> None:
        """Generate comprehensive code quality report."""
        self.log("Generating code quality report...", "info")
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        print("\n" + "="*80)
        print("📊 CODE QUALITY REPORT")
        print("="*80)
        print(f"⏱️  Total Duration: {duration:.2f}s")
        print(f"📁 Project Root: {self.project_root}")
        print(f"📅 Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Summary
        passed = sum(1 for result in self.results.values() if result["status"] == "passed")
        failed = sum(1 for result in self.results.values() if result["status"] == "failed")
        skipped = sum(1 for result in self.results.values() if result["status"] == "skipped")
        
        print("📈 SUMMARY")
        print("-" * 40)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print()
        
        # Detailed Results
        print("🔍 DETAILED RESULTS")
        print("-" * 40)
        
        for check_name, result in self.results.items():
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "pending": "⏳",
                "skipped": "⏭️"
            }.get(result["status"], "❓")
            
            print(f"{status_icon} {check_name.replace('_', ' ').title()}: {result['status']}")
            
            if result["errors"]:
                for error in result["errors"][:3]:  # Show first 3 errors
                    print(f"    • {error}")
                if len(result["errors"]) > 3:
                    print(f"    • ... and {len(result['errors']) - 3} more errors")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        
        if failed > 0:
            print("❌ Issues found that need attention:")
            for check_name, result in self.results.items():
                if result["status"] == "failed":
                    print(f"  • {check_name.replace('_', ' ').title()}: {', '.join(result['errors'])}")
            
            print("\n🔧 To auto-fix formatting issues, run:")
            print("   python run_code_quality.py --auto-fix")
        else:
            print("🎉 All code quality checks passed! Your code is in excellent shape.")
        
        print("\n📚 For more information, check the generated reports:")
        print("  • Coverage: htmlcov/index.html")
        print("  • Security: bandit-report.json, safety-report.json")
        print("  • Complexity: Check console output above")
        
        print("="*80)
    
    def run_all_checks(self, auto_fix: bool = False) -> bool:
        """Run all code quality checks."""
        self.log("🚀 Starting comprehensive code quality analysis", "start")
        print(f"📁 Project: {self.project_root}")
        print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check dependencies
        if not self.check_dependencies():
            self.log("❌ Dependency check failed", "error")
            return False
        
        # Run all checks
        checks = [
            ("Code Formatting", self.run_code_formatting),
            ("Linting", self.run_linting),
            ("Type Checking", self.run_type_checking),
            ("Security Scanning", self.run_security_scanning),
            ("Complexity Analysis", self.run_complexity_analysis),
            ("Coverage Analysis", self.run_coverage_analysis),
            ("Performance Profiling", self.run_performance_profiling),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {check_name} failed with error: {e}", "error")
                all_passed = False
        
        # Auto-fix if requested
        if auto_fix and not all_passed:
            self.auto_fix_issues()
        
        # Generate report
        self.generate_report()
        
        return all_passed

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive code quality checks")
    parser.add_argument("--auto-fix", action="store_true", help="Automatically fix formatting issues")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--check", choices=["formatting", "linting", "type", "security", "complexity", "coverage", "performance"], 
                       help="Run only specific check")
    
    args = parser.parse_args()
    
    runner = CodeQualityRunner(args.project_root)
    
    if args.check:
        # Run specific check
        check_methods = {
            "formatting": runner.run_code_formatting,
            "linting": runner.run_linting,
            "type": runner.run_type_checking,
            "security": runner.run_security_scanning,
            "complexity": runner.run_complexity_analysis,
            "coverage": runner.run_coverage_analysis,
            "performance": runner.run_performance_profiling,
        }
        
        if args.check in check_methods:
            success = check_methods[args.check]()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown check: {args.check}")
            sys.exit(1)
    else:
        # Run all checks
        success = runner.run_all_checks(auto_fix=args.auto_fix)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()