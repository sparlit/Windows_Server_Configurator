import time
import sqlite3
import pytest
import tkinter as tk
from NetworkConfigurator import NetworkConfiguratorApp

@pytest.fixture
def app_instance(tmp_path):
    db_file = str(tmp_path / "test_net.db")
    root = tk.Tk()
    root.withdraw()
    app = NetworkConfiguratorApp(root)
    app.db_path = db_file
    app.init_database()
    yield app
    root.destroy()

def test_on_fleet_department_changed_allocation(app_instance):
    app = app_instance
    app.dept_combobox.set("SERVER")  # v4_start: 1

    # Insert some allocated IP records
    conn = sqlite3.connect(app.db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
                   ("PC-1", "SERVER", "10.0.0.1", "fd37:e2a1:9c84:1000::1"))
    cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
                   ("PC-2", "SERVER", "10.0.0.2", "fd37:e2a1:9c84:1000::2"))
    cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)",
                   ("PC-3", "SERVER", "10.0.0.3", "fd37:e2a1:9c84:1000::3"))
    conn.commit()
    conn.close()

    app.on_fleet_department_changed()

    assert app.ipv4_entry.get() == "10.0.0.4"
    assert app.ipv6_entry.get() == "fd37:e2a1:9c84:1000::4"
    assert app.pc_name_entry.get() == "PC-SERVER-4"

def benchmark_allocation(num_records):
    # Pure logic benchmark function simulating line 379-386 in NetworkConfigurator.py
    v4_base = 1
    rows = [(f"10.0.0.{i}",) for i in range(1, num_records + 1)]

    # Baseline list approach
    start_time = time.perf_counter()
    allocated_v4_list = []
    for row in rows:
        try: allocated_v4_list.append(int(row[0].split('.')[-1]))
        except: pass
    next_offset_list = v4_base
    while next_offset_list in allocated_v4_list:
        next_offset_list += 1
    list_duration = time.perf_counter() - start_time

    # Optimized set approach
    start_time = time.perf_counter()
    allocated_v4_set = set()
    for row in rows:
        try: allocated_v4_set.add(int(row[0].split('.')[-1]))
        except: pass
    next_offset_set = v4_base
    while next_offset_set in allocated_v4_set:
        next_offset_set += 1
    set_duration = time.perf_counter() - start_time

    return list_duration, set_duration, next_offset_list, next_offset_set

def test_benchmark_performance():
    num_records = 10000
    list_duration, set_duration, res_list, res_set = benchmark_allocation(num_records)
    assert res_list == res_set == num_records + 1
    print(f"\n[Benchmark] Records: {num_records} | List time: {list_duration:.6f}s | Set time: {set_duration:.6f}s | Speedup: {list_duration/set_duration:.2f}x")
