import os
import sys
import csv
import sqlite3
import pytest
from unittest.mock import MagicMock, patch

import tkinter as tk
import NetworkConfigurator
from NetworkConfigurator import is_admin, NetworkConfiguratorApp


@pytest.fixture
def mock_tk_root():
    """Provides a hidden Tk root window for tests requiring GUI widgets."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def temp_db(tmp_path):
    """Provides a temporary SQLite database path."""
    db_file = tmp_path / "test_network_config_history.db"
    return str(db_file)


@pytest.fixture
def app_instance(mock_tk_root, temp_db):
    """Initializes NetworkConfiguratorApp pointing to a temporary test database and mocked subprocess."""
    with patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(stdout="Ethernet\nWi-Fi", stderr="", returncode=0)
        app = NetworkConfiguratorApp(mock_tk_root)
        app.db_path = temp_db
        app.init_database()
        yield app


# --- 1. Test is_admin ---
def test_is_admin_true():
    mock_windll = MagicMock()
    mock_windll.shell32.IsUserAnAdmin.return_value = 1
    with patch.object(sys, "platform", "win32"), patch("ctypes.windll", mock_windll, create=True):
        assert bool(is_admin()) is True


def test_is_admin_false():
    mock_windll = MagicMock()
    mock_windll.shell32.IsUserAnAdmin.return_value = 0
    with patch.object(sys, "platform", "win32"), patch("ctypes.windll", mock_windll, create=True):
        assert bool(is_admin()) is False


def test_is_admin_exception():
    with patch("NetworkConfigurator.ctypes", MagicMock()) as mock_ctypes:
        mock_ctypes.windll.shell32.IsUserAnAdmin.side_effect = Exception("OS error")
        assert is_admin() is False


# --- 2. Test Database Initialization & Basic Operations ---
def test_init_database(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allocated_profiles';")
    table = cursor.fetchone()
    conn.close()
    assert table is not None
    assert table[0] == "allocated_profiles"


def test_refresh_ledger_view(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("PC-TEST-10", "ALBUM_PRINTING", "10.0.0.10", "fd37:e2a1:9c84:1100::10"),
    )
    conn.commit()
    conn.close()

    app_instance.refresh_ledger_view()
    children = app_instance.tree.get_children()
    assert len(children) == 1
    item_values = app_instance.tree.item(children[0])["values"]
    assert item_values[0] == "PC-TEST-10"
    assert item_values[1] == "ALBUM_PRINTING"
    assert item_values[2] == "10.0.0.10"
    assert item_values[3] == "fd37:e2a1:9c84:1100::10"


# --- 3. Test Department Mapping and Auto Offset Logic ---
def test_on_fleet_department_changed_first_allocation(app_instance):
    app_instance.dept_combobox.set("ALBUM_PRINTING")
    app_instance.on_fleet_department_changed()

    assert app_instance.ipv4_entry.get() == "10.0.0.10"
    assert app_instance.ipv6_entry.get() == "fd37:e2a1:9c84:1100::10"
    assert app_instance.pc_name_entry.get() == "PC-ALBUM_PRINTING-10"


def test_on_fleet_department_changed_incremental_offset(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("PC-ALBUM_PRINTING-10", "ALBUM_PRINTING", "10.0.0.10", "fd37:e2a1:9c84:1100::10"),
    )
    conn.commit()
    conn.close()

    app_instance.dept_combobox.set("ALBUM_PRINTING")
    app_instance.on_fleet_department_changed()

    assert app_instance.ipv4_entry.get() == "10.0.0.11"
    assert app_instance.ipv6_entry.get() == "fd37:e2a1:9c84:1100::11"
    assert app_instance.pc_name_entry.get() == "PC-ALBUM_PRINTING-11"


# --- 4. Test Conflict Checking ---
def test_check_conflicts(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("PC-EXISTING", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1"),
    )
    conn.commit()
    conn.close()

    # No conflict
    is_valid, err = app_instance.check_conflicts("PC-NEW", "10.0.0.2", "fd37:e2a1:9c84:1000::2")
    assert is_valid is True
    assert err == ""

    # Hostname conflict
    is_valid, err = app_instance.check_conflicts("PC-EXISTING", "10.0.0.2", "fd37:e2a1:9c84:1000::2")
    assert is_valid is False
    assert "Ledger Collision: Hostname identity" in err

    # IPv4 conflict
    is_valid, err = app_instance.check_conflicts("PC-NEW", "10.0.0.1", "fd37:e2a1:9c84:1000::2")
    assert is_valid is False
    assert "Ledger Collision: IPv4 target" in err

    # IPv6 conflict
    is_valid, err = app_instance.check_conflicts("PC-NEW", "10.0.0.2", "fd37:e2a1:9c84:1000::1")
    assert is_valid is False
    assert "Ledger Collision: IPv6 target" in err


# --- 5. Test Individual Device Search, Override & Delete ---
def test_load_individual_record_data_found(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("PC-SEARCH", "COUNTER", "10.0.0.26", "fd37:e2a1:9c84:1200::26"),
    )
    conn.commit()
    conn.close()

    app_instance.ind_search_entry.delete(0, tk.END)
    app_instance.ind_search_entry.insert(0, "PC-SEARCH")

    with patch("tkinter.messagebox.showinfo") as mock_info:
        app_instance.load_individual_record_data()
        mock_info.assert_called_once()

    assert app_instance.ind_name_entry.get() == "PC-SEARCH"
    assert app_instance.ind_dept_combobox.get() == "COUNTER"
    assert app_instance.ind_ipv4_entry.get() == "10.0.0.26"
    assert app_instance.ind_ipv6_entry.get() == "fd37:e2a1:9c84:1200::26"


def test_load_individual_record_data_not_found(app_instance):
    app_instance.ind_search_entry.delete(0, tk.END)
    app_instance.ind_search_entry.insert(0, "NONEXISTENT")

    with patch("tkinter.messagebox.showwarning") as mock_warn:
        app_instance.load_individual_record_data()
        mock_warn.assert_called_once()


def test_save_individual_record_override(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("OLD-PC", "COUNTER", "10.0.0.26", "fd37:e2a1:9c84:1200::26"),
    )
    conn.commit()
    conn.close()

    app_instance.ind_search_entry.delete(0, tk.END)
    app_instance.ind_search_entry.insert(0, "OLD-PC")
    app_instance.ind_name_entry.delete(0, tk.END)
    app_instance.ind_name_entry.insert(0, "NEW-PC")
    app_instance.ind_dept_combobox.set("DESIGN_STUDIO")
    app_instance.ind_ipv4_entry.delete(0, tk.END)
    app_instance.ind_ipv4_entry.insert(0, "10.0.0.41")
    app_instance.ind_ipv6_entry.delete(0, tk.END)
    app_instance.ind_ipv6_entry.insert(0, "fd37:e2a1:9c84:1300::41")

    with patch("tkinter.messagebox.showinfo") as mock_info:
        app_instance.save_individual_record_override()
        mock_info.assert_called_once()

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT pc_name, department, ipv4_address, ipv6_address FROM allocated_profiles WHERE pc_name = ?", ("NEW-PC",))
    row = cursor.fetchone()
    conn.close()

    assert row == ("NEW-PC", "DESIGN_STUDIO", "10.0.0.41", "fd37:e2a1:9c84:1300::41")


def test_delete_individual_record(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("DEL-PC", "LASER_CUTTING", "10.0.0.76", "fd37:e2a1:9c84:1500::76"),
    )
    conn.commit()
    conn.close()

    app_instance.ind_search_entry.delete(0, tk.END)
    app_instance.ind_search_entry.insert(0, "DEL-PC")

    with patch("tkinter.messagebox.askyesno", return_value=True), patch("tkinter.messagebox.showinfo") as mock_info:
        app_instance.delete_individual_record()
        mock_info.assert_called_once()

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM allocated_profiles WHERE pc_name = ?", ("DEL-PC",))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


# --- 6. Test Purge DB and Export CSV ---
def test_purge_entire_database(app_instance, temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("PURGE-PC", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1"),
    )
    conn.commit()
    conn.close()

    with patch("tkinter.messagebox.askyesno", return_value=True):
        app_instance.purge_entire_database()

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM allocated_profiles")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


def test_export_ledger_to_csv(app_instance, temp_db, tmp_path):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
        ("CSV-PC", "NETWORK_ADMIN", "10.0.0.116", "fd37:e2a1:9c84:1800::116"),
    )
    conn.commit()
    conn.close()

    export_path = str(tmp_path / "ledger_export.csv")

    with patch("tkinter.filedialog.asksaveasfilename", return_value=export_path), patch("tkinter.messagebox.showinfo") as mock_info:
        app_instance.export_ledger_to_csv()
        mock_info.assert_called_once()

    assert os.path.exists(export_path)
    with open(export_path, "r") as f:
        reader = list(csv.reader(f))
        assert reader[0] == ["PC Name", "Department", "IPv4 Address", "IPv6 Address", "Provisioning Date"]
        assert reader[1][0] == "CSV-PC"
        assert reader[1][1] == "NETWORK_ADMIN"


# --- 7. Test Adapter Population and Logging ---
def test_populate_adapters_success(app_instance):
    mock_res = MagicMock(stdout="Adapter1\nAdapter2\n", stderr="", returncode=0)
    with patch("subprocess.run", return_value=mock_res):
        app_instance.populate_adapters()
        assert tuple(app_instance.adapter_combobox['values']) == ("Adapter1", "Adapter2")
        assert app_instance.adapter_combobox.get() == "Adapter1"


def test_populate_adapters_fallback_on_error(app_instance):
    with patch("subprocess.run", side_effect=Exception("Powershell unavailable")):
        app_instance.populate_adapters()
        assert tuple(app_instance.adapter_combobox['values']) == ("Ethernet",)
        assert app_instance.adapter_combobox.get() == "Ethernet"


def test_clear_logs(app_instance):
    app_instance.log_to_tab1("Test log entry")
    assert "Test log entry" in app_instance.log_text.get("1.0", tk.END)
    app_instance.clear_logs()
    assert app_instance.log_text.get("1.0", tk.END).strip() == ""


def test_auto_select_tuning_parameters(app_instance):
    app_instance.tune_jumbo.set(False)
    app_instance.tune_eee.set(False)
    app_instance.auto_select_tuning_parameters()
    assert app_instance.tune_jumbo.get() is True
    assert app_instance.tune_eee.get() is True


# --- 8. Test Startup Mounting Script Injection ---
def test_inject_startup_mounting_script(app_instance, monkeypatch, tmp_path):
    fake_appdata = str(tmp_path)
    monkeypatch.setitem(os.environ, "APPDATA", fake_appdata)

    target_dir = os.path.join(fake_appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    os.makedirs(target_dir, exist_ok=True)

    result = app_instance.inject_startup_mounting_script("Z:", "Production_Data")
    assert result is True

    script_file = os.path.join(target_dir, "MountDrives.bat")
    assert os.path.exists(script_file)

    with open(script_file, "r") as f:
        content = f.read()
        assert 'net use Z: "\\\\fd37:e2a1:9c84:1000--2.ipv6-literal.net\\Production_Data"' in content


# --- 9. Test Execution Provisioning ---
def test_execute_provisioning_validation_errors(app_instance):
    with patch("NetworkConfigurator.is_admin", return_value=True):
        app_instance.dept_combobox.set("")
        with patch("tkinter.messagebox.showerror") as mock_err:
            app_instance.execute_provisioning()
            mock_err.assert_called_with("Selection Error", "Please assign a functional group department first.")


def test_execute_provisioning_success(app_instance, temp_db):
    app_instance.dept_combobox.set("SERVER")
    app_instance.adapter_combobox.set("Ethernet")
    app_instance.pc_name_entry.delete(0, tk.END)
    app_instance.pc_name_entry.insert(0, "PC-SERVER-1")
    app_instance.ipv4_entry.delete(0, tk.END)
    app_instance.ipv4_entry.insert(0, "10.0.0.1")
    app_instance.gw_entry.delete(0, tk.END)
    app_instance.gw_entry.insert(0, "10.0.0.254")
    app_instance.ipv6_entry.delete(0, tk.END)
    app_instance.ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::1")

    with patch("NetworkConfigurator.is_admin", return_value=True), \
         patch.object(app_instance, "run_cmd", return_value=(True, "")) as mock_cmd, \
         patch.object(app_instance, "inject_startup_mounting_script", return_value=True) as mock_inject, \
         patch("tkinter.messagebox.showinfo") as mock_info:

        app_instance.execute_provisioning()

        assert mock_cmd.called
        assert mock_inject.called
        mock_info.assert_called_once()

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT pc_name, department, ipv4_address, ipv6_address FROM allocated_profiles WHERE pc_name = ?", ("PC-SERVER-1",))
    row = cursor.fetchone()
    conn.close()

    assert row == ("PC-SERVER-1", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1")
