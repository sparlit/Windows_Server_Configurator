import time
import unittest
from unittest.mock import MagicMock, patch
import sqlite3
import os
import tkinter as tk

import NetworkConfigurator

class TestFirewallOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        if os.path.exists("network_config_history.db"):
            try:
                conn = sqlite3.connect("network_config_history.db")
                conn.cursor().execute("DELETE FROM allocated_profiles WHERE pc_name LIKE 'PC-TEST-%'")
                conn.commit()
                conn.close()
            except sqlite3.OperationalError:
                pass

    def tearDown(self):
        if os.path.exists("network_config_history.db"):
            try:
                conn = sqlite3.connect("network_config_history.db")
                conn.cursor().execute("DELETE FROM allocated_profiles WHERE pc_name LIKE 'PC-TEST-%'")
                conn.commit()
                conn.close()
            except sqlite3.OperationalError:
                pass

    @patch('subprocess.run')
    def test_execute_provisioning_firewall_purging_batched(self, mock_subprocess):
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="Ethernet\n", stderr="")

        app = NetworkConfigurator.NetworkConfiguratorApp(self.root)

        # Populate UI fields to avoid validation errors in execute_provisioning
        app.adapter_combobox.set("Ethernet")
        app.dept_combobox.set("SERVER")
        app.pc_name_entry.delete(0, tk.END)
        app.pc_name_entry.insert(0, "PC-TEST-FIREWALL-1")
        app.ipv4_entry.delete(0, tk.END)
        app.ipv4_entry.insert(0, "10.0.0.252")
        app.ipv6_entry.delete(0, tk.END)
        app.ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::252")

        # Disable tuning checkboxes to focus on provisioning commands
        app.tune_jumbo.set(False)
        app.tune_eee.set(False)
        app.tune_autotune.set(False)
        app.tune_offload.set(False)
        app.tune_throttling.set(False)
        app.tune_cubic.set(False)
        app.tune_rss.set(False)
        app.tune_chimney.set(False)
        app.tune_timestamps.set(False)
        app.tune_netdma.set(False)
        app.tune_ecn.set(False)
        app.drive_letter_combobox.set("")
        app.share_folder_combobox.set("")

        mock_subprocess.reset_mock()

        # Patch messagebox and is_admin
        with patch('NetworkConfigurator.is_admin', return_value=True), \
             patch('tkinter.messagebox.showinfo'), \
             patch('tkinter.messagebox.showerror'), \
             patch('tkinter.messagebox.showwarning'):

            start_time = time.perf_counter()
            app.execute_provisioning()
            elapsed_time = time.perf_counter() - start_time

            # Filter calls to Remove-NetFirewallRule
            remove_rule_calls = [
                call for call in mock_subprocess.call_args_list
                if len(call.args) > 0 and len(call.args[0]) > 2 and "Remove-NetFirewallRule" in call.args[0][2]
            ]

            print(f"\n[BENCHMARK] Total Remove-NetFirewallRule subprocess calls: {len(remove_rule_calls)}")
            print(f"[BENCHMARK] Execution time: {elapsed_time:.6f}s")

            # Verify exactly 1 call was made to Remove-NetFirewallRule with batched display names
            self.assertEqual(len(remove_rule_calls), 1)
            expected_cmd = "Remove-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk', 'Allow-IPv4-Printers', 'Isolate-IPv6-PCs', 'Allow-IPv6-Master-Servers' -ErrorAction SilentlyContinue"
            self.assertEqual(remove_rule_calls[0].args[0][2], expected_cmd)

if __name__ == '__main__':
    unittest.main()
