import os
import tempfile
import pytest
from unittest.mock import MagicMock
from NetworkConfigurator import validate_drive_letter, validate_share_name, NetworkConfiguratorApp

def test_validate_drive_letter():
    # Valid drive letters
    assert validate_drive_letter("X:") is True
    assert validate_drive_letter("y:") is True
    assert validate_drive_letter("Z:") is True

    # Invalid drive letters
    assert validate_drive_letter("X") is False
    assert validate_drive_letter("X:\\") is False
    assert validate_drive_letter("X:\ncalc.exe") is False
    assert validate_drive_letter("X: & calc.exe") is False
    assert validate_drive_letter("") is False
    assert validate_drive_letter(None) is False

def test_validate_share_name():
    # Valid share names
    assert validate_share_name("SharedFolder") is True
    assert validate_share_name("Production_Data") is True
    assert validate_share_name("Design-Files 123") is True

    # Invalid share names (injection / traversal attempts)
    assert validate_share_name("share\ncalc.exe") is False
    assert validate_share_name("share\r\nnet use Z: \\\\attacker\\share") is False
    assert validate_share_name('share" & calc.exe') is False
    assert validate_share_name("share|whoami") is False
    assert validate_share_name("share; calc") is False
    assert validate_share_name("../etc/passwd") is False
    assert validate_share_name("share/subfolder") is False
    assert validate_share_name("share\\subfolder") is False
    assert validate_share_name("") is False
    assert validate_share_name(None) is False

def test_inject_startup_mounting_script_success(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("APPDATA", tmpdir)

        # Mock app instance without initializing full Tkinter GUI
        app = MagicMock(spec=NetworkConfiguratorApp)
        app.log_to_tab1 = MagicMock()

        # Call bound method
        result = NetworkConfiguratorApp.inject_startup_mounting_script(app, "X:", "Production_Data")
        assert result is True

        expected_script_path = os.path.join(tmpdir, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "MountDrives.bat")
        assert os.path.exists(expected_script_path)

        with open(expected_script_path, "r") as f:
            content = f.read()

        assert 'net use X: "\\\\fd37:e2a1:9c84:1000--2.ipv6-literal.net\\Production_Data"' in content
        assert 'net use Y: "\\\\fd37:e2a1:9c84:1000--3.ipv6-literal.net\\Production_Data"' in content

def test_inject_startup_mounting_script_injection_prevention(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("APPDATA", tmpdir)

        app = MagicMock(spec=NetworkConfiguratorApp)
        app.log_to_tab1 = MagicMock()

        # Attempt batch injection via share
        malicious_share = 'Production_Data"\nnet use Z: \\\\malicious\\share & calc.exe'
        result = NetworkConfiguratorApp.inject_startup_mounting_script(app, "X:", malicious_share)

        assert result is False

        expected_script_path = os.path.join(tmpdir, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "MountDrives.bat")
        assert not os.path.exists(expected_script_path)
        app.log_to_tab1.assert_called_with("⚠️ Startup Script Injection Failure: Invalid or unsafe share folder name 'Production_Data\"\nnet use Z: \\\\malicious\\share & calc.exe'.")
