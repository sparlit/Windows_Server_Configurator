import os
import sqlite3
import unittest
import tkinter as tk
from NetworkConfigurator import NetworkConfiguratorApp

class TestNetworkConfigurator(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_unit.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.root = tk.Tk()
        self.app = NetworkConfiguratorApp(self.root)
        self.app.db_path = self.db_path
        self.app.init_database()

    def tearDown(self):
        self.root.destroy()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_department_change_next_ip(self):
        self.app.dept_combobox.set("COUNTER")
        self.app.on_fleet_department_changed()

        # COUNTER v4_start is 26
        self.assertEqual(self.app.ipv4_entry.get(), "10.0.0.26")
        self.assertEqual(self.app.pc_name_entry.get(), "PC-COUNTER-26")

        # Insert allocated profile for 26
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
                       ("PC-COUNTER-26", "COUNTER", "10.0.0.26", "fd37:e2a1:9c84:1200::26"))
        conn.commit()
        conn.close()

        # Invalidate cache if needed when app changes dept
        if hasattr(self.app, 'invalidate_cache'):
            self.app.invalidate_cache()

        self.app.on_fleet_department_changed()
        self.assertEqual(self.app.ipv4_entry.get(), "10.0.0.27")
        self.assertEqual(self.app.pc_name_entry.get(), "PC-COUNTER-27")

if __name__ == "__main__":
    unittest.main()
