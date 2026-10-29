import unittest
import os
import sqlite3
import time
import tempfile
import tkinter as tk
import NetworkConfigurator

class TestNetworkConfigurator(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.db_fd)

        self.root = tk.Tk()
        self.app = NetworkConfigurator.NetworkConfiguratorApp(self.root)
        self.app.db_path = self.db_path
        self.app.init_database()

    def tearDown(self):
        self.root.destroy()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def populate_dummy_data(self, count=1000):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        depts = list(self.app.departments.keys())
        for i in range(count):
            dept = depts[i % len(depts)]
            pc_name = f"PC-TEST-{i}"
            ip4 = f"10.0.{(i // 250)}.{i % 250}"
            ip6 = f"fd37:e2a1:9c84:1000::{i}"
            cursor.execute(
                "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
                (pc_name, dept, ip4, ip6)
            )
        conn.commit()
        conn.close()
        self.app.refresh_ledger_view()

    def test_department_changed_correctness(self):
        self.populate_dummy_data(count=90)
        self.app.dept_combobox.set("ALBUM_PRINTING")
        self.app.on_fleet_department_changed()

        # Check that ipv4, ipv6, pc_name entries were updated
        ip4_val = self.app.ipv4_entry.get()
        self.assertTrue(ip4_val.startswith("10.0.0."))
        self.assertEqual(self.app.pc_name_entry.get(), f"PC-ALBUM_PRINTING-{ip4_val.split('.')[-1]}")

    def test_cache_invalidation_and_consistency(self):
        # Verify cache updates when entries are added or deleted
        dept = "ALBUM_PRINTING"
        v4_start = self.app.departments[dept]["v4_start"]

        self.app.dept_combobox.set(dept)
        self.app.on_fleet_department_changed()
        self.assertEqual(self.app.ipv4_entry.get(), f"10.0.0.{v4_start}")

        # Insert a profile into database manually and refresh ledger
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-ALBUM_PRINTING-10", dept, f"10.0.0.{v4_start}", "fd37:e2a1:9c84:1100::10")
        )
        conn.commit()
        conn.close()

        self.app.refresh_ledger_view()
        self.app.on_fleet_department_changed()
        self.assertEqual(self.app.ipv4_entry.get(), f"10.0.0.{v4_start + 1}")

    def test_benchmark_department_change(self):
        self.populate_dummy_data(count=1000)

        depts = list(self.app.departments.keys())
        iterations = 500

        start_time = time.perf_counter()
        for i in range(iterations):
            dept = depts[i % len(depts)]
            self.app.dept_combobox.set(dept)
            self.app.on_fleet_department_changed()
        end_time = time.perf_counter()

        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000
        print(f"\n[BENCHMARK RESULT] {iterations} department changes executed in {total_time:.4f} seconds ({avg_time_ms:.4f} ms per change)")

if __name__ == '__main__':
    unittest.main()
