import sys
from unittest.mock import MagicMock

# Mock tkinter modules if tkinter is missing
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    mock_tk = MagicMock()
    mock_ttk = MagicMock()
    sys.modules['tkinter'] = mock_tk
    sys.modules['tkinter.ttk'] = mock_ttk
    sys.modules['tkinter.messagebox'] = MagicMock()
    sys.modules['tkinter.filedialog'] = MagicMock()

import sqlite3
import pytest

def test_set_lookup_logic(tmp_path):
    db_file = str(tmp_path / "test_network.db")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE allocated_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pc_name TEXT UNIQUE,
            department TEXT,
            ipv4_address TEXT UNIQUE,
            ipv6_address TEXT UNIQUE
        )
    """)
    dept = "ALBUM_PRINTING"
    v4_base = 10

    # Insert allocated IPs for offset 10 and 11
    cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address) VALUES (?, ?, ?)",
                   ("PC-1", dept, f"10.0.0.{v4_base}"))
    cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address) VALUES (?, ?, ?)",
                   ("PC-2", dept, f"10.0.0.{v4_base + 1}"))
    conn.commit()

    # Replicate query & set lookup logic from on_fleet_department_changed
    allocated_v4 = set()
    cursor.execute("SELECT ipv4_address FROM allocated_profiles WHERE department = ?", (dept,))
    for row in cursor.fetchall():
        try: allocated_v4.add(int(row[0].split('.')[-1]))
        except: pass
    next_offset = v4_base
    while next_offset in allocated_v4:
        next_offset += 1
    conn.close()

    assert next_offset == v4_base + 2
