import time
import os
import sqlite3
import tkinter as tk
from NetworkConfigurator import NetworkConfiguratorApp

def create_mock_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
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

    # Populate with sample data across departments
    departments = ["ALBUM_PRINTING", "COUNTER", "DESIGN_STUDIO", "FLATBED_PRINTING", "LASER_CUTTING", "LASER_PRINTING", "MANAGING_DIRECTOR", "NETWORK_ADMIN", "SERVER"]
    for dept_idx, dept in enumerate(departments):
        for i in range(50):
            pc_name = f"PC-{dept}-{i}"
            ip4 = f"10.0.{dept_idx}.{i+1}"
            ip6 = f"fd37:e2a1:9c84:{1000+dept_idx}::{i+1}"
            cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)", (pc_name, dept, ip4, ip6))
    conn.commit()
    conn.close()

def run_benchmark():
    db_path = "test_benchmark.db"
    create_mock_db(db_path)

    root = tk.Tk()
    app = NetworkConfiguratorApp(root)
    app.db_path = db_path

    # Run repeated calls to on_fleet_department_changed
    departments = list(app.departments.keys())
    iterations = 2000

    start_time = time.perf_counter()
    for i in range(iterations):
        dept = departments[i % len(departments)]
        app.dept_combobox.set(dept)
        app.on_fleet_department_changed()
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    print(f"Benchmark completed: {iterations} department changes took {elapsed:.4f} seconds ({elapsed/iterations*1000:.4f} ms/op)")

    root.destroy()
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    run_benchmark()
