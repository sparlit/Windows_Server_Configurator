import time
import subprocess
import unittest
from unittest.mock import MagicMock, patch
import os
import uuid

if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":99"

import NetworkConfigurator

class TestNetworkConfigurator(unittest.TestCase):
    def test_execute_provisioning_firewall_batching(self):
        """Verify that execute_provisioning invokes run_cmd with batched Remove-NetFirewallRule."""
        import tkinter as tk
        root = tk.Tk()
        app = NetworkConfigurator.NetworkConfiguratorApp(root)

        uid = str(uuid.uuid4())[:8]
        pc_name = f"PC-TEST-{uid}"
        ipv4 = f"10.0.99.{int(uid, 16) % 250 + 1}"
        ipv6 = f"fd37:e2a1:9c84:1000::{uid}"

        app.dept_combobox.set("SERVER")
        app.adapter_combobox.set("Ethernet")
        app.pc_name_entry.insert(0, pc_name)
        app.ipv4_entry.insert(0, ipv4)
        app.ipv6_entry.insert(0, ipv6)

        executed_cmds = []
        def mock_run_cmd(cmd):
            executed_cmds.append(cmd)
            return True, ""

        app.run_cmd = mock_run_cmd

        # Patch is_admin to True, APPDATA env, and messagebox to skip UI prompts
        with patch("NetworkConfigurator.is_admin", return_value=True), \
             patch("NetworkConfigurator.NetworkConfiguratorApp.check_conflicts", return_value=(True, "")), \
             patch.dict(os.environ, {"APPDATA": "/tmp"}), \
             patch("tkinter.messagebox.showinfo"), \
             patch("tkinter.messagebox.showerror"):
            app.execute_provisioning()

        expected_batched_cmd = "Remove-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk', 'Allow-IPv4-Printers', 'Isolate-IPv6-PCs', 'Allow-IPv6-Master-Servers' -ErrorAction SilentlyContinue"

        self.assertIn(expected_batched_cmd, executed_cmds)
        root.destroy()

    def test_subprocess_overhead_benchmark(self):
        """Benchmark process execution overhead difference between 4 subprocess invocations vs 1."""
        start_4 = time.perf_counter()
        for _ in range(4):
            subprocess.run(["python3", "-c", "pass"], capture_output=True)
        duration_4 = time.perf_counter() - start_4

        start_1 = time.perf_counter()
        subprocess.run(["python3", "-c", "pass"], capture_output=True)
        duration_1 = time.perf_counter() - start_1

        print(f"\n[BENCHMARK] 4 Subprocess Calls: {duration_4 * 1000:.2f}ms | 1 Subprocess Call: {duration_1 * 1000:.2f}ms")
        print(f"[BENCHMARK] Speedup: {duration_4 / duration_1:.2f}x reduction in process creation overhead")
        self.assertLess(duration_1, duration_4)

if __name__ == "__main__":
    unittest.main()
