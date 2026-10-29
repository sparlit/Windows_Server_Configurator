import pytest
import os
import unittest.mock as mock
from NetworkConfigurator import (
    escape_ps_arg,
    validate_pc_name,
    validate_adapter,
    validate_ipv4,
    validate_ipv6,
    validate_ipv6_subnet,
    validate_printers,
    validate_drive_letter,
    validate_share_folder,
)

def test_escape_ps_arg():
    assert escape_ps_arg("Ethernet") == "Ethernet"
    assert escape_ps_arg("PC'Name") == "PC''Name"
    assert escape_ps_arg("Test'; Calc.exe; '") == "Test''; Calc.exe; ''"
    assert escape_ps_arg(None) == ""

def test_validate_pc_name():
    assert validate_pc_name("PC-ADMIN-10") is True
    assert validate_pc_name("DESKTOP123") is True
    assert validate_pc_name("") is True
    # Command injection payloads / invalid characters
    assert validate_pc_name("PC'; Remove-Item C:\\ -Recurse -Force; '") is False
    assert validate_pc_name("PC&whoami") is False
    assert validate_pc_name("PC|calc") is False
    assert validate_pc_name("PC$Name") is False

def test_validate_adapter():
    assert validate_adapter("Ethernet") is True
    assert validate_adapter("Wi-Fi 2") is True
    assert validate_adapter("Ethernet (vSwitch)") is True
    assert validate_adapter("") is False
    # Command injection payloads
    assert validate_adapter("Ethernet'; Start-Process calc.exe; '") is False
    assert validate_adapter("Ethernet`whoami`") is False

def test_validate_ipv4():
    assert validate_ipv4("10.0.0.10") is True
    assert validate_ipv4("192.168.1.1") is True
    assert validate_ipv4("256.0.0.1") is False
    assert validate_ipv4("10.0.0.1; calc.exe") is False
    assert validate_ipv4("") is False

def test_validate_ipv6():
    assert validate_ipv6("fd37:e2a1:9c84:1000::10") is True
    assert validate_ipv6("::1") is True
    assert validate_ipv6("fd37:e2a1:9c84:1000::10; calc.exe") is False
    assert validate_ipv6("invalid_ipv6") is False

def test_validate_ipv6_subnet():
    assert validate_ipv6_subnet("fd37:e2a1:9c84:1000::/64") is True
    assert validate_ipv6_subnet("") is True
    assert validate_ipv6_subnet("fd37:e2a1:9c84:1000::/64; Invoke-Expression") is False

def test_validate_printers():
    assert validate_printers("10.0.0.200,10.0.0.201") is True
    assert validate_printers("10.0.0.1-10.0.0.253") is True
    assert validate_printers("") is True
    assert validate_printers("10.0.0.200; Remove-Item") is False

def test_validate_drive_letter():
    assert validate_drive_letter("X:") is True
    assert validate_drive_letter("Z:") is True
    assert validate_drive_letter("X: & calc.exe") is False

def test_validate_share_folder():
    assert validate_share_folder("Production_Data") is True
    assert validate_share_folder("SharedFolder-1") is True
    assert validate_share_folder("Share&dir") is False

@mock.patch("NetworkConfigurator.is_admin", return_value=True)
@mock.patch("NetworkConfigurator.messagebox.showerror")
def test_execute_provisioning_blocks_injection(mock_showerror, mock_is_admin):
    import tkinter as tk
    from NetworkConfigurator import NetworkConfiguratorApp

    # Setup headless Tkinter root
    os.environ["DISPLAY"] = ":99"
    try:
        root = tk.Tk()
    except Exception:
        pytest.skip("Tkinter display not available")

    app = NetworkConfiguratorApp(root)

    # Set up fields with a command injection payload in pc_name
    app.dept_combobox.set("NETWORK_ADMIN")
    app.adapter_combobox.set("Ethernet")
    app.pc_name_entry.delete(0, tk.END)
    app.pc_name_entry.insert(0, "PC'; Start-Process calc.exe; '")
    app.ipv4_entry.delete(0, tk.END)
    app.ipv4_entry.insert(0, "10.0.0.116")
    app.gw_entry.delete(0, tk.END)
    app.gw_entry.insert(0, "10.0.0.254")
    app.ipv6_entry.delete(0, tk.END)
    app.ipv6_entry.insert(0, "fd37:e2a1:9c84:1800::116")

    with mock.patch.object(app, "run_cmd") as mock_run_cmd:
        app.execute_provisioning()
        # Ensure run_cmd was NOT called due to validation failure
        mock_run_cmd.assert_not_called()
        mock_showerror.assert_called_once()
        assert "Validation Error" in mock_showerror.call_args[0][0]

    root.destroy()
