import os
import sqlite3
import tempfile
import csv
import unittest
from unittest.mock import patch, MagicMock, mock_open
import ctypes

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pytest

import NetworkConfigurator
from NetworkConfigurator import is_admin, NetworkConfiguratorApp


class TestIsAdmin(unittest.TestCase):
    def test_is_admin_true(self):
        mock_windll = MagicMock()
        mock_windll.shell32.IsUserAnAdmin.return_value = True
        with patch.object(ctypes, "windll", mock_windll, create=True):
            self.assertTrue(is_admin())

    def test_is_admin_false(self):
        mock_windll = MagicMock()
        mock_windll.shell32.IsUserAnAdmin.return_value = False
        with patch.object(ctypes, "windll", mock_windll, create=True):
            self.assertFalse(is_admin())

    def test_is_admin_exception(self):
        mock_windll = MagicMock()
        mock_windll.shell32.IsUserAnAdmin.side_effect = Exception("Not Windows")
        with patch.object(ctypes, "windll", mock_windll, create=True):
            self.assertFalse(is_admin())


class TestNetworkConfiguratorApp(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for each test
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)

        # Patch db_path in NetworkConfiguratorApp during initialization
        with patch.object(NetworkConfiguratorApp, "populate_adapters"), \
             patch.object(NetworkConfiguratorApp, "refresh_ledger_view"):
            self.root = tk.Tk()
            self.root.withdraw()
            self.app = NetworkConfiguratorApp(self.root)
            self.app.db_path = self.temp_db_path
            self.app.init_database()

    def tearDown(self):
        self.root.destroy()
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_init_database(self):
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allocated_profiles'")
        table = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(table)
        self.assertEqual(table[0], "allocated_profiles")

    def test_log_to_tab1_and_clear_logs(self):
        self.app.clear_logs()
        self.assertEqual(self.app.log_text.get("1.0", tk.END).strip(), "")

        self.app.log_to_tab1("Test log message")
        self.assertIn("Test log message", self.app.log_text.get("1.0", tk.END))

        self.app.clear_logs()
        self.assertEqual(self.app.log_text.get("1.0", tk.END).strip(), "")

    def test_auto_select_tuning_parameters(self):
        # Unset variables
        self.app.tune_jumbo.set(False)
        self.app.tune_eee.set(False)
        self.app.auto_select_tuning_parameters()
        self.assertTrue(self.app.tune_jumbo.get())
        self.assertTrue(self.app.tune_eee.get())
        self.assertTrue(self.app.tune_autotune.get())

    def test_check_conflicts(self):
        # Seed DB
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-EXISTING", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1")
        )
        conn.commit()
        conn.close()

        # No conflicts
        valid, msg = self.app.check_conflicts("PC-NEW", "10.0.0.2", "fd37:e2a1:9c84:1000::2")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

        # Conflict on Hostname
        valid, msg = self.app.check_conflicts("PC-EXISTING", "10.0.0.2", "fd37:e2a1:9c84:1000::2")
        self.assertFalse(valid)
        self.assertIn("Hostname identity", msg)

        # Conflict on IPv4
        valid, msg = self.app.check_conflicts("PC-NEW", "10.0.0.1", "fd37:e2a1:9c84:1000::2")
        self.assertFalse(valid)
        self.assertIn("IPv4 target", msg)

        # Conflict on IPv6
        valid, msg = self.app.check_conflicts("PC-NEW", "10.0.0.2", "fd37:e2a1:9c84:1000::1")
        self.assertFalse(valid)
        self.assertIn("IPv6 target", msg)

    def test_on_fleet_department_changed(self):
        # Test department change without prior records
        self.app.dept_combobox.set("SERVER")
        self.app.on_fleet_department_changed()

        self.assertEqual(self.app.ipv4_entry.get(), "10.0.0.1")
        self.assertEqual(self.app.ipv6_entry.get(), "fd37:e2a1:9c84:1000::1")
        self.assertEqual(self.app.pc_name_entry.get(), "PC-SERVER-1")

        # Seed existing allocation
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-SERVER-1", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1")
        )
        conn.commit()
        conn.close()

        # Check next available increment
        self.app.on_fleet_department_changed()
        self.assertEqual(self.app.ipv4_entry.get(), "10.0.0.2")
        self.assertEqual(self.app.ipv6_entry.get(), "fd37:e2a1:9c84:1000::2")
        self.assertEqual(self.app.pc_name_entry.get(), "PC-SERVER-2")

    def test_refresh_ledger_view(self):
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-TEST", "COUNTER", "10.0.0.26", "fd37:e2a1:9c84:1200::26")
        )
        conn.commit()
        conn.close()

        self.app.refresh_ledger_view()
        children = self.app.tree.get_children()
        self.assertEqual(len(children), 1)
        item_values = self.app.tree.item(children[0])["values"]
        self.assertEqual(item_values[0], "PC-TEST")
        self.assertEqual(item_values[1], "COUNTER")

    @patch("tkinter.messagebox.askyesno", return_value=True)
    def test_purge_entire_database(self, mock_ask):
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-PURGE", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1")
        )
        conn.commit()
        conn.close()

        self.app.purge_entire_database()

        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM allocated_profiles")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    @patch("tkinter.filedialog.asksaveasfilename")
    @patch("tkinter.messagebox.showinfo")
    def test_export_ledger_to_csv(self, mock_info, mock_saveas):
        temp_csv_fd, temp_csv_path = tempfile.mkstemp(suffix=".csv")
        os.close(temp_csv_fd)
        try:
            mock_saveas.return_value = temp_csv_path

            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
                ("PC-EXPORT", "DESIGN_STUDIO", "10.0.0.41", "fd37:e2a1:9c84:1300::41")
            )
            conn.commit()
            conn.close()

            self.app.export_ledger_to_csv()
            mock_info.assert_called_once()

            with open(temp_csv_path, "r", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
                self.assertEqual(rows[0], ["PC Name", "Department", "IPv4 Address", "IPv6 Address", "Provisioning Date"])
                self.assertEqual(rows[1][0], "PC-EXPORT")
                self.assertEqual(rows[1][1], "DESIGN_STUDIO")
        finally:
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)

    @patch("tkinter.messagebox.showinfo")
    def test_load_individual_record_data_found(self, mock_info):
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-IND", "DESIGN_STUDIO", "10.0.0.41", "fd37:e2a1:9c84:1300::41")
        )
        conn.commit()
        conn.close()

        self.app.ind_search_entry.delete(0, tk.END)
        self.app.ind_search_entry.insert(0, "PC-IND")
        self.app.load_individual_record_data()

        self.assertEqual(self.app.ind_name_entry.get(), "PC-IND")
        self.assertEqual(self.app.ind_dept_combobox.get(), "DESIGN_STUDIO")
        self.assertEqual(self.app.ind_ipv4_entry.get(), "10.0.0.41")
        self.assertEqual(self.app.ind_ipv6_entry.get(), "fd37:e2a1:9c84:1300::41")
        self.assertEqual(str(self.app.save_override_btn["state"]), "normal")

    @patch("tkinter.messagebox.showwarning")
    def test_load_individual_record_data_not_found(self, mock_warn):
        self.app.ind_search_entry.delete(0, tk.END)
        self.app.ind_search_entry.insert(0, "NONEXISTENT")
        self.app.load_individual_record_data()
        mock_warn.assert_called_once()

    @patch("tkinter.messagebox.showinfo")
    def test_save_individual_record_override(self, mock_info):
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-OLD", "DESIGN_STUDIO", "10.0.0.41", "fd37:e2a1:9c84:1300::41")
        )
        conn.commit()
        conn.close()

        self.app.ind_search_entry.delete(0, tk.END)
        self.app.ind_search_entry.insert(0, "PC-OLD")
        self.app.ind_name_entry.delete(0, tk.END)
        self.app.ind_name_entry.insert(0, "PC-NEW-NAME")
        self.app.ind_dept_combobox.set("FLATBED_PRINTING")
        self.app.ind_ipv4_entry.delete(0, tk.END)
        self.app.ind_ipv4_entry.insert(0, "10.0.0.61")
        self.app.ind_ipv6_entry.delete(0, tk.END)
        self.app.ind_ipv6_entry.insert(0, "fd37:e2a1:9c84:1400::61")

        self.app.save_individual_record_override()

        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT pc_name, department, ipv4_address FROM allocated_profiles WHERE pc_name = 'PC-NEW-NAME'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "FLATBED_PRINTING")
        self.assertEqual(row[2], "10.0.0.61")

    @patch("tkinter.messagebox.askyesno", return_value=True)
    @patch("tkinter.messagebox.showinfo")
    def test_delete_individual_record(self, mock_info, mock_ask):
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
            ("PC-DEL", "DESIGN_STUDIO", "10.0.0.41", "fd37:e2a1:9c84:1300::41")
        )
        conn.commit()
        conn.close()

        self.app.ind_search_entry.delete(0, tk.END)
        self.app.ind_search_entry.insert(0, "PC-DEL")
        self.app.delete_individual_record()

        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM allocated_profiles WHERE pc_name = 'PC-DEL'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    @patch("subprocess.run")
    def test_populate_adapters_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Ethernet0\nWi-Fi\n"
        mock_run.return_value = mock_result

        self.app.populate_adapters()
        self.assertEqual(tuple(self.app.adapter_combobox["values"]), ("Ethernet0", "Wi-Fi"))
        self.assertEqual(self.app.adapter_combobox.get(), "Ethernet0")

    @patch("subprocess.run", side_effect=Exception("PowerShell Error"))
    def test_populate_adapters_fallback(self, mock_run):
        self.app.populate_adapters()
        self.assertEqual(tuple(self.app.adapter_combobox["values"]), ("Ethernet",))
        self.assertEqual(self.app.adapter_combobox.get(), "Ethernet")

    @patch("subprocess.run")
    def test_run_cmd(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "Command Executed"
        mock_run.return_value = mock_result

        success, output = self.app.run_cmd("Get-Process")
        self.assertTrue(success)
        self.assertEqual(output, "Command Executed")

    def test_inject_startup_mounting_script(self):
        with patch.dict(os.environ, {"APPDATA": "/tmp"}):
            with patch("builtins.open", mock_open()) as mock_file:
                result = self.app.inject_startup_mounting_script("X:", "Production_Data")
                self.assertTrue(result)
                mock_file.assert_called_once()
                handle = mock_file()
                handle.write.assert_called_once()
                written_content = handle.write.call_args[0][0]
                self.assertIn("Mounting File Server 1 (GDC Core Lane) to X:...", written_content)
                self.assertIn("Production_Data", written_content)

    @patch("NetworkConfigurator.is_admin", return_value=True)
    @patch.object(NetworkConfiguratorApp, "run_cmd", return_value=(True, "OK"))
    @patch("tkinter.messagebox.showinfo")
    def test_execute_provisioning_success(self, mock_info, mock_run_cmd, mock_admin):
        with patch.dict(os.environ, {"APPDATA": "/tmp"}):
            with patch("builtins.open", mock_open()):
                self.app.adapter_combobox.set("Ethernet")
                self.app.dept_combobox.set("SERVER")
                self.app.pc_name_entry.delete(0, tk.END)
                self.app.pc_name_entry.insert(0, "PC-SERVER-TEST")
                self.app.ipv4_entry.delete(0, tk.END)
                self.app.ipv4_entry.insert(0, "10.0.0.100")
                self.app.gw_entry.delete(0, tk.END)
                self.app.gw_entry.insert(0, "10.0.0.254")
                self.app.ipv6_entry.delete(0, tk.END)
                self.app.ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::100")

                self.app.execute_provisioning()

                # Check database record was created
                conn = sqlite3.connect(self.temp_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT pc_name, department FROM allocated_profiles WHERE pc_name = 'PC-SERVER-TEST'")
                row = cursor.fetchone()
                conn.close()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], "PC-SERVER-TEST")
                self.assertEqual(row[1], "SERVER")
                mock_info.assert_called_once()
