import time
import unittest
from unittest.mock import MagicMock, patch

# Baseline implementation as in NetworkConfigurator.py:524
def purge_baseline_original(run_cmd_func):
    for rule in ['Block-Local-IPv4-CrossTalk', 'Allow-IPv4-Printers', 'Isolate-IPv6-PCs', 'Allow-IPv6-Master-Servers']:
        run_cmd_func(f"Remove-NetFirewallRule -DisplayName '{rule}' -ErrorAction SilentlyContinue")

# Batched implementation
def purge_baseline_optimized(run_cmd_func):
    rules = ["'Block-Local-IPv4-CrossTalk'", "'Allow-IPv4-Printers'", "'Isolate-IPv6-PCs'", "'Allow-IPv6-Master-Servers'"]
    rules_str = ", ".join(rules)
    run_cmd_func(f"Remove-NetFirewallRule -DisplayName {rules_str} -ErrorAction SilentlyContinue")

class TestFirewallPurgeBenchmark(unittest.TestCase):
    def test_call_counts(self):
        mock_run_cmd_orig = MagicMock(return_value=(True, ""))
        purge_baseline_original(mock_run_cmd_orig)
        self.assertEqual(mock_run_cmd_orig.call_count, 4)

        mock_run_cmd_opt = MagicMock(return_value=(True, ""))
        purge_baseline_optimized(mock_run_cmd_opt)
        self.assertEqual(mock_run_cmd_opt.call_count, 1)
        mock_run_cmd_opt.assert_called_once_with(
            "Remove-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk', 'Allow-IPv4-Printers', 'Isolate-IPv6-PCs', 'Allow-IPv6-Master-Servers' -ErrorAction SilentlyContinue"
        )

    def test_benchmark_simulation(self):
        # Simulate a small delay per process execution (e.g., 10ms per subprocess)
        def mock_process_execution(cmd):
            time.sleep(0.010)
            return True, ""

        start_orig = time.perf_counter()
        purge_baseline_original(mock_process_execution)
        dur_orig = time.perf_counter() - start_orig

        start_opt = time.perf_counter()
        purge_baseline_optimized(mock_process_execution)
        dur_opt = time.perf_counter() - start_opt

        print(f"\n[BENCHMARK] Original baseline purge duration: {dur_orig*1000:.2f} ms (4 subprocess calls)")
        print(f"[BENCHMARK] Optimized batched purge duration:  {dur_opt*1000:.2f} ms (1 subprocess call)")
        print(f"[BENCHMARK] Speedup: {dur_orig/dur_opt:.2f}x reduction in subprocess calls and overhead")

        self.assertLess(dur_opt, dur_orig)

if __name__ == '__main__':
    unittest.main()
