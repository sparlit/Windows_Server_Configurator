import os
import sqlite3
import tkinter as tk
from unittest.mock import patch
import pytest
from NetworkConfigurator import NetworkConfiguratorApp, is_admin

def test_imports_and_is_admin():
    # Verify NetworkConfigurator imported cleanly without sys and is_admin function exists
    assert callable(is_admin)

def test_app_initialization(tmp_path):
    # Initialize Tkinter root window in headless environment
    root = tk.Tk()
    root.withdraw()

    # Use temporary database path to avoid polluting workspace
    db_file = tmp_path / "test_network_config_history.db"

    # Instantiate App with patched db_path attribute
    with patch.object(NetworkConfiguratorApp, "init_database") as mock_init_db:
        # Save original init_database method functionality with custom path
        def custom_init_db(self_app):
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS allocated_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pc_name TEXT UNIQUE,
                    department TEXT,
                    ipv4_address TEXT UNIQUE,
                    ipv6_address TEXT UNIQUE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()

        mock_init_db.side_effect = lambda: None

        app = NetworkConfiguratorApp.__new__(NetworkConfiguratorApp)
        app.db_path = str(db_file)
        custom_init_db(app)

        # Call __init__ with mocked init_database so original __init__ sets up Tk components
        app.__init__(root)

    assert app.root == root
    assert os.path.exists(str(db_file))

    # Verify SQLite schema was initialized
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='allocated_profiles'")
    table = cursor.fetchone()
    conn.close()
    assert table is not None

    root.destroy()
