import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import NetworkConfigurator

class DummyWidget:
    def __init__(self, value=""):
        self._value = value
    def get(self):
        return self._value
    def set(self, val):
        self._value = val
    def delete(self, *args):
        self._value = ""
    def insert(self, idx, val):
        self._value = val
    def config(self, **kwargs):
        pass

class TestTCPTuningHeadless(unittest.TestCase):
    def setUp(self):
        self.db_path = "/tmp/test_network_config_history.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_app(self):
        os.environ["APPDATA"] = "/tmp"

        app = object.__new__(NetworkConfigurator.NetworkConfiguratorApp)

        app.adapter_combobox = DummyWidget("Ethernet")
        app.dept_combobox = DummyWidget("SERVER")
        app.pc_name_entry = DummyWidget("TEST-PC-999")
        app.ipv4_entry = DummyWidget("10.0.0.99")
        app.gw_entry = DummyWidget("10.0.0.254")
        app.ipv6_entry = DummyWidget("fd37:e2a1:9c84:1000::99")

        app.srv_ipv6_entry = DummyWidget("fd37:e2a1:9c84:1000::/64")
        app.printers_entry = DummyWidget("10.0.0.200,10.0.0.201")
        app.drive_letter_combobox = DummyWidget("X:")
        app.share_folder_combobox = DummyWidget("Production_Data")

        app.tune_autotune = DummyWidget(False)
        app.tune_cubic = DummyWidget(False)
        app.tune_rss = DummyWidget(False)
        app.tune_chimney = DummyWidget(False)
        app.tune_timestamps = DummyWidget(False)
        app.tune_netdma = DummyWidget(False)
        app.tune_ecn = DummyWidget(False)
        app.tune_throttling = DummyWidget(False)
        app.tune_jumbo = DummyWidget(False)
        app.tune_eee = DummyWidget(False)
        app.tune_offload = DummyWidget(False)

        app.apply_btn = DummyWidget()
        app.db_path = self.db_path

        app.init_database()
        app.log_to_tab1 = lambda msg: None
        app.refresh_ledger_view = lambda: None

        return app

    def test_tcp_tuning_consolidated_single_call(self):
        app = self._create_app()

        # Enable all 7 TCP options
        app.tune_autotune.set(True)
        app.tune_cubic.set(True)
        app.tune_rss.set(True)
        app.tune_chimney.set(True)
        app.tune_timestamps.set(True)
        app.tune_netdma.set(True)
        app.tune_ecn.set(True)

        commands_run = []
        def mock_run_cmd(cmd):
            commands_run.append(cmd)
            return True, ""

        app.run_cmd = mock_run_cmd

        with patch("NetworkConfigurator.is_admin", return_value=True), \
             patch("NetworkConfigurator.messagebox.showinfo"), \
             patch("NetworkConfigurator.messagebox.askyesno", return_value=True):

            start_time = time.perf_counter()
            app.execute_provisioning()
            elapsed = time.perf_counter() - start_time

        netsh_cmds = [cmd for cmd in commands_run if "netsh int tcp set global" in cmd]
        print(f"\n[OPTIMIZED BENCHMARK]")
        print(f"Total netsh tcp run_cmd calls: {len(netsh_cmds)}")
        for i, cmd in enumerate(netsh_cmds):
            print(f"  Command {i+1}: {cmd}")
        print(f"Execution time: {elapsed:.6f} seconds")

        # Expect exactly 1 consolidated run_cmd call containing all 7 settings
        self.assertEqual(len(netsh_cmds), 1)
        single_cmd = netsh_cmds[0]
        self.assertIn("autotuninglevel=normal", single_cmd)
        self.assertIn("congestionprovider=cubic", single_cmd)
        self.assertIn("rss=enabled", single_cmd)
        self.assertIn("chimney=enabled", single_cmd)
        self.assertIn("timestamps=disabled", single_cmd)
        self.assertIn("netdma=enabled", single_cmd)
        self.assertIn("ecncapability=enabled", single_cmd)

    def test_tcp_tuning_subset(self):
        app = self._create_app()

        # Enable only autotune and rss
        app.tune_autotune.set(True)
        app.tune_rss.set(True)

        commands_run = []
        app.run_cmd = lambda cmd: (commands_run.append(cmd), (True, ""))[1]

        with patch("NetworkConfigurator.is_admin", return_value=True), \
             patch("NetworkConfigurator.messagebox.showinfo"), \
             patch("NetworkConfigurator.messagebox.askyesno", return_value=True):
            app.execute_provisioning()

        netsh_cmds = [cmd for cmd in commands_run if "netsh int tcp set global" in cmd]
        self.assertEqual(len(netsh_cmds), 1)
        self.assertEqual(netsh_cmds[0], "netsh int tcp set global autotuninglevel=normal; netsh int tcp set global rss=enabled")

if __name__ == "__main__":
    unittest.main()
