#!/usr/bin/env python3
"""
VAPT Toolkit — Phase 6 Manual Testing Framework
Tracks and manages manual test execution
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class TestStatus(Enum):
    """Test execution status."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"

class DefectSeverity(Enum):
    """Defect severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class DefectPriority(Enum):
    """Defect priority levels."""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

class DefectStatus(Enum):
    """Defect status workflow."""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"

@dataclass
class TestCase:
    """Represents a single test case."""
    test_id: str
    test_name: str
    category: str  # WS, API, REP, UX
    environment: str
    description: str
    status: TestStatus = TestStatus.NOT_STARTED
    execution_date: Optional[str] = None
    tester_name: Optional[str] = None
    expected_result: str = ""
    actual_result: str = ""
    notes: str = ""
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "category": self.category,
            "environment": self.environment,
            "description": self.description,
            "status": self.status.value,
            "execution_date": self.execution_date,
            "tester_name": self.tester_name,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "notes": self.notes,
            "screenshot_path": self.screenshot_path,
        }

@dataclass
class Defect:
    """Represents a defect/bug found during testing."""
    defect_id: str
    title: str
    description: str
    severity: DefectSeverity
    priority: DefectPriority
    status: DefectStatus = DefectStatus.NEW
    related_test_id: Optional[str] = None
    found_date: Optional[str] = None
    finder_name: Optional[str] = None
    assigned_to: Optional[str] = None
    steps_to_reproduce: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    environment: str = ""
    resolution: str = ""
    resolved_date: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "defect_id": self.defect_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "related_test_id": self.related_test_id,
            "found_date": self.found_date,
            "finder_name": self.finder_name,
            "assigned_to": self.assigned_to,
            "steps_to_reproduce": self.steps_to_reproduce,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "environment": self.environment,
            "resolution": self.resolution,
            "resolved_date": self.resolved_date,
        }

class TestTracker:
    """Manages test case execution and tracking."""
    
    def __init__(self, output_dir: str = "test_results"):
        """Initialize test tracker."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_cases: List[TestCase] = []
        self.defects: List[Defect] = []
        
        self.results_file = self.output_dir / "test_results.json"
        self.defects_file = self.output_dir / "defects.json"
        
        self._load_existing_results()
    
    def _load_existing_results(self):
        """Load existing test results if available."""
        if self.results_file.exists():
            with open(self.results_file) as f:
                data = json.load(f)
                for item in data.get("test_cases", []):
                    item["status"] = TestStatus(item["status"])
                    self.test_cases.append(TestCase(**item))
        
        if self.defects_file.exists():
            with open(self.defects_file) as f:
                data = json.load(f)
                for item in data.get("defects", []):
                    item["severity"] = DefectSeverity(item["severity"])
                    item["priority"] = DefectPriority(item["priority"])
                    item["status"] = DefectStatus(item["status"])
                    self.defects.append(Defect(**item))
    
    def add_test_case(self, test_case: TestCase):
        """Add a test case to tracking."""
        # Check if already exists
        existing = next((t for t in self.test_cases if t.test_id == test_case.test_id), None)
        if existing:
            self.test_cases.remove(existing)
        self.test_cases.append(test_case)
        self.save_results()
    
    def add_defect(self, defect: Defect):
        """Add a defect to tracking."""
        existing = next((d for d in self.defects if d.defect_id == defect.defect_id), None)
        if existing:
            self.defects.remove(existing)
        self.defects.append(defect)
        self.save_defects()
    
    def update_test_status(self, test_id: str, status: TestStatus, 
                          actual_result: str = "", notes: str = ""):
        """Update test case status."""
        test = next((t for t in self.test_cases if t.test_id == test_id), None)
        if not test:
            print(f"❌ Test {test_id} not found")
            return
        
        test.status = status
        test.actual_result = actual_result
        test.notes = notes
        test.execution_date = datetime.now().isoformat()
        self.save_results()
        print(f"✅ Updated {test_id}: {status.value}")
    
    def save_results(self):
        """Save test results to JSON."""
        data = {
            "total_tests": len(self.test_cases),
            "timestamp": datetime.now().isoformat(),
            "test_cases": [t.to_dict() for t in self.test_cases],
        }
        with open(self.results_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def save_defects(self):
        """Save defects to JSON."""
        data = {
            "total_defects": len(self.defects),
            "timestamp": datetime.now().isoformat(),
            "defects": [d.to_dict() for d in self.defects],
        }
        with open(self.defects_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def export_to_csv(self):
        """Export test results to CSV."""
        csv_file = self.output_dir / "test_results.csv"
        
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "test_id", "test_name", "category", "environment",
                "status", "tester_name", "execution_date", "notes"
            ])
            writer.writeheader()
            for test in sorted(self.test_cases, key=lambda t: t.test_id):
                writer.writerow({
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "category": test.category,
                    "environment": test.environment,
                    "status": test.status.value,
                    "tester_name": test.tester_name or "",
                    "execution_date": test.execution_date or "",
                    "notes": test.notes or "",
                })
        
        print(f"✅ Exported test results to {csv_file}")
    
    def get_statistics(self) -> Dict:
        """Calculate test statistics."""
        total = len(self.test_cases)
        passed = len([t for t in self.test_cases if t.status == TestStatus.PASS])
        failed = len([t for t in self.test_cases if t.status == TestStatus.FAIL])
        blocked = len([t for t in self.test_cases if t.status == TestStatus.BLOCKED])
        not_started = len([t for t in self.test_cases if t.status == TestStatus.NOT_STARTED])
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        defect_stats = {
            "critical": len([d for d in self.defects if d.severity == DefectSeverity.CRITICAL]),
            "high": len([d for d in self.defects if d.severity == DefectSeverity.HIGH]),
            "medium": len([d for d in self.defects if d.severity == DefectSeverity.MEDIUM]),
            "low": len([d for d in self.defects if d.severity == DefectSeverity.LOW]),
        }
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "blocked": blocked,
            "not_started": not_started,
            "pass_rate": f"{pass_rate:.1f}%",
            "defects": defect_stats,
            "total_defects": len(self.defects),
        }
    
    def print_summary(self):
        """Print test summary."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("VAPT TOOLKIT - MANUAL TESTING SUMMARY")
        print("="*60)
        print(f"\n📊 Test Execution Summary:")
        print(f"  Total Tests:    {stats['total_tests']}")
        print(f"  Passed:         {stats['passed']}")
        print(f"  Failed:         {stats['failed']}")
        print(f"  Blocked:        {stats['blocked']}")
        print(f"  Not Started:    {stats['not_started']}")
        print(f"  Pass Rate:      {stats['pass_rate']}")
        
        print(f"\n🐛 Defect Summary:")
        print(f"  Total Defects:  {stats['total_defects']}")
        print(f"  Critical:       {stats['defects']['critical']}")
        print(f"  High:           {stats['defects']['high']}")
        print(f"  Medium:         {stats['defects']['medium']}")
        print(f"  Low:            {stats['defects']['low']}")
        
        print("\n" + "="*60)

def create_default_test_cases() -> List[TestCase]:
    """Create default test cases from manual testing guide."""
    categories = {
        "WS": [
            ("WS-001", "SQL Injection Detection", "Basic SQL injection detection in login forms"),
            ("WS-002", "Reflected XSS Detection", "Detection of reflected cross-site scripting"),
            ("WS-003", "Stored XSS Detection", "Detection of stored XSS vulnerabilities"),
            ("WS-004", "CSRF Detection", "CSRF vulnerability detection"),
            ("WS-005", "IDOR Detection", "Insecure Direct Object Reference detection"),
            ("WS-006", "Authentication Bypass", "Detection of authentication bypass vectors"),
            ("WS-007", "Insecure Cookies", "Cookie security analysis"),
            ("WS-008", "Missing Security Headers", "Detection of missing HTTP security headers"),
            ("WS-009", "File Upload Vulnerabilities", "File upload security testing"),
            ("WS-010", "Path Traversal", "Directory traversal vulnerability detection"),
            ("WS-011", "Command Injection", "OS command injection detection"),
            ("WS-012", "XXE Injection", "XML external entity injection detection"),
            ("WS-013", "SSRF Detection", "Server-side request forgery detection"),
            ("WS-014", "Open Redirect", "Open redirect vulnerability detection"),
            ("WS-015", "Information Disclosure", "Sensitive information disclosure detection"),
        ],
        "API": [
            ("API-001", "API Key Authentication", "API key authentication validation"),
            ("API-002", "Rate Limiting", "API rate limiting enforcement"),
            ("API-003", "Bulk Scanning", "Bulk scanning API functionality"),
            ("API-004", "Export Functionality", "Multiple export format support"),
            ("API-005", "Webhook Delivery", "Webhook event delivery and retry logic"),
        ],
        "REP": [
            ("REP-001", "PDF Report Generation", "PDF report generation and content"),
            ("REP-002", "Excel Export", "Excel export formatting and data"),
            ("REP-003", "Scan Comparison", "Vulnerability comparison between scans"),
            ("REP-004", "Heat Map Rendering", "Interactive heat map visualization"),
            ("REP-005", "Executive Report", "Executive summary report generation"),
        ],
        "UX": [
            ("UX-001", "Scope Editor Workflow", "Scope editor functionality and UX"),
            ("UX-002", "Theme Switching", "Theme switching and persistence"),
            ("UX-003", "Notification Delivery", "Real-time notification delivery"),
            ("UX-004", "Schedule Creation/Execution", "Scan scheduling and execution"),
            ("UX-005", "Search/Filter Functionality", "Search and filter operations"),
        ],
    }
    
    test_cases = []
    
    for category, tests in categories.items():
        for test_id, test_name, description in tests:
            env = "DVWA+Juice Shop+WebGoat" if category == "WS" else "VAPT Toolkit"
            test_case = TestCase(
                test_id=test_id,
                test_name=test_name,
                category=category,
                environment=env,
                description=description,
            )
            test_cases.append(test_case)
    
    return test_cases

if __name__ == "__main__":
    # Initialize tracker
    tracker = TestTracker("test_results")
    
    # Add default test cases if not already present
    if len(tracker.test_cases) == 0:
        default_tests = create_default_test_cases()
        for test in default_tests:
            tracker.add_test_case(test)
        print(f"✅ Added {len(default_tests)} default test cases")
    
    # Print summary
    tracker.print_summary()
    
    # Export results
    tracker.export_to_csv()
    
    print("\n📁 Test results saved to: test_results/")
    print("   - test_results.json")
    print("   - test_results.csv")
    print("   - defects.json")
