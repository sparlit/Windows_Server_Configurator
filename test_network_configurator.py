import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import time
import os
import sqlite3
from NetworkConfigurator import NetworkConfiguratorApp

class TestNetworkConfiguratorTuning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.db_path = "test_network_config_history.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.app = NetworkConfiguratorApp(self.root)
        self.app.db_path = self.db_path
        self.app.init_database()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch.dict(os.environ, {"APPDATA": "/tmp"}, clear=False)
    @patch("NetworkConfigurator.is_admin", return_value=True)
    @patch("NetworkConfigurator.messagebox")
    @patch.object(NetworkConfiguratorApp, "run_cmd", return_value=(True, ""))
    def test_tcp_tuning_benchmark(self, mock_run_cmd, mock_messagebox, mock_is_admin):
        # Setup form data
        self.app.dept_combobox.set("SERVER")
        self.app.pc_name_entry.delete(0, tk.END)
        self.app.pc_name_entry.insert(0, "TEST-PC-1")
        self.app.ipv4_entry.delete(0, tk.END)
        self.app.ipv4_entry.insert(0, "10.0.0.1")
        self.app.ipv6_entry.delete(0, tk.END)
        self.app.ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::1")

        # Select all TCP options
        self.app.tune_autotune.set(True)
        self.app.tune_cubic.set(True)
        self.app.tune_rss.set(True)
        self.app.tune_chimney.set(True)
        self.app.tune_timestamps.set(True)
        self.app.tune_netdma.set(True)
        self.app.tune_ecn.set(True)

        start_time = time.perf_counter()
        self.app.execute_provisioning()
        elapsed_time = time.perf_counter() - start_time

        # Extract netsh calls made to run_cmd
        netsh_calls = [call.args[0] for call in mock_run_cmd.call_args_list if "netsh int tcp set global" in call.args[0]]
        print(f"\n[BENCHMARK] Total run_cmd calls with netsh: {len(netsh_calls)}")
        for idx, call in enumerate(netsh_calls, 1):
            print(f"  Call {idx}: {call}")

        self.assertEqual(len(netsh_calls), 1)
        expected_combined = (
            "netsh int tcp set global autotuninglevel=normal; "
            "netsh int tcp set global congestionprovider=cubic; "
            "netsh int tcp set global rss=enabled; "
            "netsh int tcp set global chimney=enabled; "
            "netsh int tcp set global timestamps=disabled; "
            "netsh int tcp set global netdma=enabled; "
            "netsh int tcp set global ecncapability=enabled"
        )
        self.assertEqual(netsh_calls[0], expected_combined)

    @patch.dict(os.environ, {"APPDATA": "/tmp"}, clear=False)
    @patch("NetworkConfigurator.is_admin", return_value=True)
    @patch("NetworkConfigurator.messagebox")
    @patch.object(NetworkConfiguratorApp, "run_cmd", return_value=(True, ""))
    def test_tcp_tuning_partial_selection(self, mock_run_cmd, mock_messagebox, mock_is_admin):
        # Setup form data
        self.app.dept_combobox.set("SERVER")
        self.app.pc_name_entry.delete(0, tk.END)
        self.app.pc_name_entry.insert(0, "TEST-PC-2")
        self.app.ipv4_entry.delete(0, tk.END)
        self.app.ipv4_entry.insert(0, "10.0.0.2")
        self.app.ipv6_entry.delete(0, tk.END)
        self.app.ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::2")

        # Select only autotune and ecn
        self.app.tune_autotune.set(True)
        self.app.tune_cubic.set(False)
        self.app.tune_rss.set(False)
        self.app.tune_chimney.set(False)
        self.app.tune_timestamps.set(False)
        self.app.tune_netdma.set(False)
        self.app.tune_ecn.set(True)

        self.app.execute_provisioning()

        netsh_calls = [call.args[0] for call in mock_run_cmd.call_args_list if "netsh int tcp set global" in call.args[0]]
        self.assertEqual(len(netsh_calls), 1)
        expected_partial = "netsh int tcp set global autotuninglevel=normal; netsh int tcp set global ecncapability=enabled"
        self.assertEqual(netsh_calls[0], expected_partial)

if __name__ == "__main__":
    unittest.main()
