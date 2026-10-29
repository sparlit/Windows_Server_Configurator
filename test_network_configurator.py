import unittest
from unittest.mock import MagicMock, patch
import sys

# Create dummy tkinter modules for testing if tkinter is not installed in the environment
if "tkinter" not in sys.modules:
    tk_mock = MagicMock()
    ttk_mock = MagicMock()
    messagebox_mock = MagicMock()
    filedialog_mock = MagicMock()

    sys.modules["tkinter"] = tk_mock
    sys.modules["tkinter.ttk"] = ttk_mock
    sys.modules["tkinter.messagebox"] = messagebox_mock
    sys.modules["tkinter.filedialog"] = filedialog_mock

import NetworkConfigurator
from NetworkConfigurator import (
    validate_ipv4,
    validate_ipv6,
    validate_ipv6_subnet,
    validate_printers_v4,
    validate_hostname,
    validate_adapter_name,
    ps_quote
)

class TestValidationAndSecurity(unittest.TestCase):
    def test_validate_ipv4(self):
        self.assertTrue(validate_ipv4("10.0.0.1"))
        self.assertTrue(validate_ipv4("192.168.1.254"))
        self.assertFalse(validate_ipv4("10.0.0.256"))
        self.assertFalse(validate_ipv4("10.0.0.1; Remove-Item -Recurse C:\\"))
        self.assertFalse(validate_ipv4("invalid-ip"))

    def test_validate_ipv6(self):
        self.assertTrue(validate_ipv6("fd37:e2a1:9c84:1000::10"))
        self.assertTrue(validate_ipv6("2001:db8::1"))
        self.assertFalse(validate_ipv6("fd37:e2a1:9c84:1000::gggg"))
        self.assertFalse(validate_ipv6("fd37::1; Invoke-Expression 'whoami'"))

    def test_validate_ipv6_subnet(self):
        self.assertTrue(validate_ipv6_subnet("fd37:e2a1:9c84:1000::/64"))
        self.assertTrue(validate_ipv6_subnet("fd37:e2a1:9c84:1000::10"))
        self.assertTrue(validate_ipv6_subnet(""))
        self.assertFalse(validate_ipv6_subnet("fd37:e2a1:9c84:1000::/64' -Confirm:$false"))

    def test_validate_printers_v4(self):
        self.assertTrue(validate_printers_v4("10.0.0.200,10.0.0.201"))
        self.assertTrue(validate_printers_v4("10.0.0.200-10.0.0.210"))
        self.assertTrue(validate_printers_v4("10.0.0.0/24"))
        self.assertTrue(validate_printers_v4(""))
        self.assertFalse(validate_printers_v4("10.0.0.200; Remove-Item C:\\"))

    def test_validate_hostname(self):
        self.assertTrue(validate_hostname("PC-SERVER-1"))
        self.assertTrue(validate_hostname("PC_01"))
        self.assertTrue(validate_hostname(""))
        self.assertFalse(validate_hostname("PC; Remove-Computer"))
        self.assertFalse(validate_hostname("PC' -NewName 'EVIL"))

    def test_validate_adapter_name(self):
        self.assertTrue(validate_adapter_name("Ethernet"))
        self.assertTrue(validate_adapter_name("Wi-Fi (2)"))
        self.assertFalse(validate_adapter_name(""))
        self.assertFalse(validate_adapter_name("Ethernet' -Confirm:$false"))

    def test_ps_quote(self):
        self.assertEqual(ps_quote("Ethernet"), "Ethernet")
        self.assertEqual(ps_quote("Test'String"), "Test''String")
        self.assertEqual(ps_quote(None), "")

class TestExecuteProvisioningValidation(unittest.TestCase):
    @patch("NetworkConfigurator.is_admin", return_value=True)
    def test_execute_provisioning_rejects_invalid_ip(self, mock_is_admin):
        app = MagicMock()
        app.adapter_combobox.get.return_value = "Ethernet"
        app.dept_combobox.get.return_value = "SERVER"
        app.pc_name_entry.get.return_value = "PC-SERVER-1"
        app.ipv4_entry.get.return_value = "10.0.0.1; Evil-Command"
        app.gw_entry.get.return_value = "10.0.0.254"
        app.ipv6_entry.get.return_value = "fd37:e2a1:9c84:1000::10"
        app.srv_ipv6_entry.get.return_value = "fd37:e2a1:9c84:1000::/64"
        app.printers_entry.get.return_value = "10.0.0.200"

        with patch("NetworkConfigurator.messagebox.showerror") as mock_showerror, \
             patch.object(NetworkConfigurator.NetworkConfiguratorApp, "run_cmd") as mock_run_cmd:
            NetworkConfigurator.NetworkConfiguratorApp.execute_provisioning(app)
            mock_showerror.assert_called_with("Validation Error", "Invalid Static IPv4 Address: 10.0.0.1; Evil-Command")
            mock_run_cmd.assert_not_called()

if __name__ == "__main__":
    unittest.main()
