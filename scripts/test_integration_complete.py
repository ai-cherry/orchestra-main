#!/usr/bin/env python3
"""Comprehensive test suite for Roo integration"""

import sys
import json
import sqlite3
from pathlib import Path

class IntegrationTester:
    """Test all integration components"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_total = 0
    
    def test(self, name, condition, details=""):
        """Run a single test"""
        self.tests_total += 1
        if condition:
            print(f"✅ {name}")
            self.tests_passed += 1
        else:
            print(f"❌ {name}")
            if details:
                print(f"   Details: {details}")
        return condition
    
    def test_database(self):
        """Test database functionality"""
        print("\n📊 Testing Database...")
        
        db_path = Path("roo_integration.db")
        self.test("Database exists", db_path.exists())
        
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            self.test("Tables created", len(tables) >= 2, f"Found {len(tables)} tables")
            
            # Test insert
            cursor.execute(
                "INSERT INTO mode_executions (mode_name, input_data, output_data) VALUES (?, ?, ?)",
                ("test", '{"test": true}', '{"result": "success"}')
            )
            conn.commit()
            
            # Test query
            cursor.execute("SELECT COUNT(*) FROM mode_executions")
            count = cursor.fetchone()[0]
            self.test("Data insertion works", count > 0, f"Found {count} records")
            
            conn.close()
    
    def test_mode_files(self):
        """Test Roo mode files"""
        print("\n🎭 Testing Roo Modes...")
        
        modes_dir = Path(".roo/modes")
        self.test("Modes directory exists", modes_dir.exists())
        
        if modes_dir.exists():
            mode_files = list(modes_dir.glob("*.json"))
            self.test("Mode files found", len(mode_files) > 0, f"Found {len(mode_files)} modes")
            
            # Test mode file validity
            valid_modes = 0
            for mode_file in mode_files[:3]:  # Test first 3
                try:
                    with open(mode_file) as f:
                        json.load(f)
                    valid_modes += 1
                except:
                    pass
            
            self.test("Mode files valid JSON", valid_modes > 0, f"{valid_modes} valid modes")
    
    def test_scripts(self):
        """Test integration scripts"""
        print("\n🔧 Testing Scripts...")
        
        scripts = [
            "scripts/roo_integration_standalone.py",
            "scripts/auto_mode_selector.py",
            "scripts/parallel_mode_executor.py"
        ]
        
        for script in scripts:
            script_path = Path(script)
            self.test(f"{script} exists", script_path.exists())
    
    def test_enhancements(self):
        """Test enhancement implementations"""
        print("\n🚀 Testing Enhancements...")
        
        # Test auto-mode selector
        try:
            sys.path.insert(0, "scripts")
            from auto_mode_selector import AutoModeSelector
            
            mode, score = AutoModeSelector.suggest_mode("debug the error in my code")
            self.test("Auto-mode selector works", mode == "debug", f"Selected: {mode}")
        except Exception as e:
            self.test("Auto-mode selector works", False, str(e))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🔍 Running Comprehensive Integration Tests\n")
        
        self.test_database()
        self.test_mode_files()
        self.test_scripts()
        self.test_enhancements()
        
        print(f"\n📊 Test Summary: {self.tests_passed}/{self.tests_total} passed")
        
        if self.tests_passed == self.tests_total:
            print("\n✅ All tests passed! Integration is working!")
            return True
        else:
            print(f"\n⚠️  {self.tests_total - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = IntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
