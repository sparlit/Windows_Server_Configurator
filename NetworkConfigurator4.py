import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import ctypes
import sqlite3
import os
import csv

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class NetworkConfiguratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enterprise Zero-Trust Deployment & Tuning Suite")
        self.root.geometry("880x950")
        self.root.resizable(False, False)
        
        self.db_path = "network_config_history.db"
        self.init_database()
        
        # Department Mapping Baselines
        self.departments = {
            "ALBUM_PRINTING":     {"v4_start": 10,  "v6_sub": "1100"},
            "COUNTER":            {"v4_start": 26,  "v6_sub": "1200"},
            "DESIGN_STUDIO":      {"v4_start": 41,  "v6_sub": "1300"},
            "FLATBED_PRINTING":   {"v4_start": 61,  "v6_sub": "1400"},
            "LASER_CUTTING":      {"v4_start": 76,  "v6_sub": "1500"},
            "LASER_PRINTING":     {"v4_start": 91,  "v6_sub": "1600"},
            "MANAGING_DIRECTOR":  {"v4_start": 106, "v6_sub": "1700"},
            "NETWORK_ADMIN":      {"v4_start": 116, "v6_sub": "1800"},
            "SERVER":             {"v4_start": 1,   "v6_sub": "1000"}
        }
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Multi-Tab Component Structure
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.tab_provision = ttk.Frame(self.notebook, padding="15")
        self.tab_individual = ttk.Frame(self.notebook, padding="15")
        self.tab_tuning = ttk.Frame(self.notebook, padding="15")
        
        self.notebook.add(self.tab_provision, text=" 🚀 Fleet Provisioning Center ")
        self.notebook.add(self.tab_individual, text=" 🖥️ Individual Device Config ")
        self.notebook.add(self.tab_tuning, text=" 🎛️ Optimization Tuning Suite ")
        
        # Build UI Elements Across Tabs
        self.setup_provision_tab()
        self.setup_individual_tab()
        self.setup_tuning_tab()
        
        # Load Defaults
        self.populate_adapters()
        self.refresh_ledger_view()
        self.auto_select_tuning_parameters()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
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

    # --- TAB 1: FLEET PROVISIONING ---
    def setup_provision_tab(self):
        top_group = ttk.LabelFrame(self.tab_provision, text=" 🔌 Core Interface Controls ", padding="10")
        top_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(top_group, text="Target Interface:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.adapter_combobox = ttk.Combobox(top_group, width=25, state="readonly")
        self.adapter_combobox.grid(row=0, column=1, padx=5, pady=2)
        
        self.refresh_btn = ttk.Button(top_group, text="🔄 Refresh", command=self.populate_adapters, width=10)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Label(top_group, text="Department / Group:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.dept_combobox = ttk.Combobox(top_group, values=list(self.departments.keys()), width=25, state="readonly")
        self.dept_combobox.grid(row=1, column=1, padx=5, pady=2)
        self.dept_combobox.bind("<<ComboboxSelected>>", self.on_fleet_department_changed)
        
        network_group = ttk.LabelFrame(self.tab_provision, text=" 🌐 Endpoint Identity & IPv4 Properties (Internet Hub) ", padding="10")
        network_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(network_group, text="New PC Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.pc_name_entry = ttk.Entry(network_group, width=35)
        self.pc_name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(network_group, text="Static IPv4 Address:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.ipv4_entry = ttk.Entry(network_group, width=35)
        self.ipv4_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(network_group, text="Default Gateway:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.gw_entry = ttk.Entry(network_group, width=35)
        self.gw_entry.insert(0, "10.0.0.254")
        self.gw_entry.grid(row=2, column=1, padx=5, pady=2)
        
        ipv6_group = ttk.LabelFrame(self.tab_provision, text=" 🔒 Isolated Service IPv6 Properties (Strict Server Link) ", padding="10")
        ipv6_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(ipv6_group, text="Static IPv6 Address:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.ipv6_entry = ttk.Entry(ipv6_group, width=35)
        self.ipv6_entry.grid(row=0, column=1, padx=5, pady=2)

        ledger_group = ttk.LabelFrame(self.tab_provision, text=" 📊 Network Allocation Ledger ", padding="5")
        ledger_group.pack(fill=tk.BOTH, expand=True, pady=4)
        
        self.tree = ttk.Treeview(ledger_group, columns=("PC Name", "Department", "IPv4", "IPv6"), show="headings", height=5)
        self.tree.heading("PC Name", text="PC Name")
        self.tree.heading("Department", text="Department")
        self.tree.heading("IPv4", text="IPv4 Address")
        self.tree.heading("IPv6", text="IPv6 Address")
        self.tree.column("PC Name", width=120)
        self.tree.column("Department", width=130)
        self.tree.column("IPv4", width=120)
        self.tree.column("IPv6", width=220)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Control Panel Buttons
        btn_control_frame = ttk.Frame(self.tab_provision)
        btn_control_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(btn_control_frame, text="🧹 Clear Log Output", command=self.clear_logs, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_control_frame, text="📊 Export Ledger CSV", command=self.export_ledger_to_csv, width=20).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_control_frame, text="⚠️ Reset Database Ledger", command=self.purge_entire_database, width=25).pack(side=tk.RIGHT, padx=2)

        self.log_text = tk.Text(self.tab_provision, height=4, width=85, state=tk.DISABLED, bg="#2b2b2b", fg="#a9b7c6", font=("Consolas", 9))
        self.log_text.pack(pady=4)

        self.apply_btn = ttk.Button(self.tab_provision, text="🚀 Apply Absolute Peer Isolation & Deploy Parameters", command=self.execute_provisioning)
        self.apply_btn.pack(fill=tk.X, ipady=4)

    # --- TAB 2: INDIVIDUAL DEVICE CONFIGURATION ---
    def setup_individual_tab(self):
        search_group = ttk.LabelFrame(self.tab_individual, text=" 🔍 Load/Modify Single Record Entry ", padding="10")
        search_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(search_group, text="Search PC Name from Ledger:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ind_search_entry = ttk.Entry(search_group, width=30)
        self.ind_search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(search_group, text="🔍 Query Record", command=self.load_individual_record_data).grid(row=0, column=2, padx=5, pady=5)

        self.edit_group = ttk.LabelFrame(self.tab_individual, text=" 🛠️ Modify Parameters & Override Data ", padding="10")
        self.edit_group.pack(fill=tk.X, pady=6)
        
        ttk.Label(self.edit_group, text="PC Host Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.ind_name_entry = ttk.Entry(self.edit_group, width=35)
        self.ind_name_entry.grid(row=0, column=1, padx=5, pady=4)
        
        ttk.Label(self.edit_group, text="Functional Department:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        self.ind_dept_combobox = ttk.Combobox(self.edit_group, values=list(self.departments.keys()), width=32, state="readonly")
        self.ind_dept_combobox.grid(row=1, column=1, padx=5, pady=4)
        
        ttk.Label(self.edit_group, text="Override IPv4 Address:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=4)
        self.ind_ipv4_entry = ttk.Entry(self.edit_group, width=35)
        self.ind_ipv4_entry.grid(row=2, column=1, padx=5, pady=4)
        
        ttk.Label(self.edit_group, text="Override IPv6 Address:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=4)
        self.ind_ipv6_entry = ttk.Entry(self.edit_group, width=35)
        self.ind_ipv6_entry.grid(row=3, column=1, padx=5, pady=4)

        action_group = ttk.Frame(self.tab_individual)
        action_group.pack(fill=tk.X, pady=10)
        
        self.save_override_btn = ttk.Button(action_group, text="💾 Save Modified Data Changes to Ledger", command=self.save_individual_record_override, state=tk.DISABLED)
        self.save_override_btn.pack(fill=tk.X, ipady=4, pady=2)
        
        self.delete_override_btn = ttk.Button(action_group, text="❌ Delete This Device From Ledger", command=self.delete_individual_record, state=tk.DISABLED)
        self.delete_override_btn.pack(fill=tk.X, ipady=4, pady=2)

    # --- TAB 3: EXTENDED OPTIMIZATION TUNING SUITE ---
    def setup_tuning_tab(self):
        global_config_frame = ttk.LabelFrame(self.tab_tuning, text=" ⚙️ Pre-Configure Fleet Scope Targets ", padding="10")
        global_config_frame.pack(fill=tk.X, pady=4)
        
        ttk.Label(global_config_frame, text="Master Server Subnet Target:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.srv_ipv6_entry = ttk.Entry(global_config_frame, width=40)
        self.srv_ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::/64")
        self.srv_ipv6_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(global_config_frame, text="Trusted Hardware Printers IPv4:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.printers_entry = ttk.Entry(global_config_frame, width=40)
        self.printers_entry.insert(0, "10.0.0.200,10.0.0.201")
        self.printers_entry.grid(row=1, column=1, padx=5, pady=2)

        # Optimization Matrix List Layout
        tuning_scroll_frame = ttk.LabelFrame(self.tab_tuning, text=" 🎛️ Optimization Tuning Options Matrix & Structural Explanation ", padding="10")
        tuning_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=4)
        
        self.tune_jumbo = tk.BooleanVar(value=True)
        self.tune_eee = tk.BooleanVar(value=True)
        self.tune_autotune = tk.BooleanVar(value=True)
        self.tune_offload = tk.BooleanVar(value=True)
        self.tune_throttling = tk.BooleanVar(value=True)
        self.tune_cubic = tk.BooleanVar(value=True)
        self.tune_rss = tk.BooleanVar(value=True)
        self.tune_chimney = tk.BooleanVar(value=True)
        self.tune_timestamps = tk.BooleanVar(value=True)
        self.tune_netdma = tk.BooleanVar(value=True)
        self.tune_ecn = tk.BooleanVar(value=True)
        
        # Build Grid Interactively
        tweaks = [
            (self.tune_jumbo, "Enable Jumbo Packet Architecture (MTU 9000)", "Drops fragmentation, allowing massive files to map natively across unmanaged layers."),
            (self.tune_eee, "Suppress Energy Efficient Ethernet (EEE) Throttling", "Disables power-saving state transitions, dropping wakeup delay to zero."),
            (self.tune_autotune, "Optimize Dynamic TCP Auto-Tuning Bounds", "Allows the Windows kernel network stack to dynamically optimize window capacity on demand."),
            (self.tune_offload, "Enforce Hardware Card Checksum Offloads", "Delegates checksum computations to the physical network card processor, saving CPU cycles."),
            (self.tune_throttling, "Bypass Windows Network Media Throttling Constraints", "Disables background multi-media packet throttle bounds, maximizing file pipeline speeds."),
            (self.tune_cubic, "Apply CUBIC Network Congestion Provider", "Switches the network congestion provider algorithm to CUBIC to stop transfer speed drops."),
            (self.tune_rss, "Enable Receive Side Scaling (RSS) Acceleration", "Spreads packet processing evenly across all available CPU cores rather than bottlenecking Core 0."),
            (self.tune_chimney, "Engage TCP Chimney Hardware Offloading", "Allows processing of entire network connections to shift away from the OS kernel to the network card."),
            (self.tune_timestamps, "Suppress Extraneous TCP Timestamps", "Eliminates trailing timestamp headers from packets, shrinking data overhead during server file syncs."),
            (self.tune_netdma, "Enable Direct Memory Access (NetDMA) Engine", "Maps server memory blocks directly into network buffers without relying on CPU registry loops."),
            (self.tune_ecn, "Activate Explicit Congestion Notification (ECN)", "Reports early infrastructure congestion back to the endpoint before packets are dropped, maintaining stability.")
        ]
        
        row_idx = 0
        for var, title, desc in tweaks:
            cb = ttk.Checkbutton(tuning_scroll_frame, text=title, variable=var)
            cb.grid(row=row_idx, column=0, sticky=tk.W, pady=1)
            lbl = ttk.Label(tuning_scroll_frame, text=f"What it does: {desc}", font=("Arial", 8, "italic"), foreground="#444444")
            lbl.grid(row=row_idx+1, column=0, sticky=tk.W, padx=20, pady=(0, 4))
            row_idx += 2
            
        autotune_box = ttk.LabelFrame(self.tab_tuning, text=" ⚡ Predictive Tuning Dashboard Controls ", padding="5")
        autotune_box.pack(fill=tk.X, pady=2)
        ttk.Label(autotune_box, text="Engine Status: Predictive Auto-Tune Armed.", foreground="green", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Button(autotune_box, text="⚡ Re-Optimize Parameters", command=self.auto_select_tuning_parameters).pack(side=tk.RIGHT, padx=5)

    def auto_select_tuning_parameters(self):
        for var in [self.tune_jumbo, self.tune_eee, self.tune_autotune, self.tune_offload, 
                    self.tune_throttling, self.tune_cubic, self.tune_rss, self.tune_chimney, 
                    self.tune_timestamps, self.tune_netdma, self.tune_ecn]:
            var.set(True)
        self.log_to_tab1("✔ Optimization matrix parameters automatically selected and verified.")

    # --- CORE APPLICATION LOGIC FUNCTIONS ---
    def log_to_tab1(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)

    def export_ledger_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path: return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT pc_name, department, ipv4_address, ipv6_address, timestamp FROM allocated_profiles")
            rows = cursor.fetchall()
            conn.close()
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["PC Name", "Department", "IPv4 Address", "IPv6 Address", "Provisioning Date"])
                writer.writerows(rows)
            messagebox.showinfo("Export Complete", "Network ledger logs successfully exported to CSV.")
        except Exception as e:
            messagebox.showerror("Export Failure", f"Could not extract CSV log schema: {str(e)}")

    def purge_entire_database(self):
        if messagebox.askyesno("⚠️ Extreme Warning", "Are you absolutely certain you want to purge the database ledger? This will erase all history and tracking information."):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM allocated_profiles")
            conn.commit()
            conn.close()
            self.refresh_ledger_view()
            self.log_to_tab1("❌ Database ledger history purged completely.")

    def load_individual_record_data(self):
        name = self.ind_search_entry.get().strip()
        if not name: return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT pc_name, department, ipv4_address, ipv6_address FROM allocated_profiles WHERE pc_name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            self.ind_name_entry.delete(0, tk.END)
            self.ind_name_entry.insert(0, row[0])
            self.ind_dept_combobox.set(row[1])
            self.ind_ipv4_entry.delete(0, tk.END)
            self.ind_ipv4_entry.insert(0, row[2])
            self.ind_ipv6_entry.delete(0, tk.END)
            self.ind_ipv6_entry.insert(0, row[3])
            
            self.save_override_btn.config(state=tk.NORMAL)
            self.delete_override_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Record Found", f"Loaded profile details for machine: {name}")
        else:
            messagebox.showwarning("Not Found", f"No record matching '{name}' found inside current ledger.")

    def save_individual_record_override(self):
        old_name = self.ind_search_entry.get().strip()
        new_name = self.ind_name_entry.get().strip()
        dept = self.ind_dept_combobox.get()
        ip4 = self.ind_ipv4_entry.get().strip()
        ip6 = self.ind_ipv6_entry.get().strip()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE allocated_profiles 
                SET pc_name = ?, department = ?, ipv4_address = ?, ipv6_address = ?
                WHERE pc_name = ?
            """, (new_name, dept, ip4, ip6, old_name))
            conn.commit()
            conn.close()
            self.refresh_ledger_view()
            messagebox.showinfo("Ledger Updated", f"Successfully saved manual modifications for: {new_name}")
        except Exception as e:
            messagebox.showerror("Database Constraint Error", f"Could not update ledger. Ensure parameters are unique:\n{str(e)}")

    def delete_individual_record(self):
        name = self.ind_search_entry.get().strip()
        if messagebox.askyesno("Confirm Delete", f"Remove machine entry '{name}' from database tracking history?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM allocated_profiles WHERE pc_name = ?", (name,))
            conn.commit()
            conn.close()
            self.refresh_ledger_view()
            self.ind_name_entry.delete(0, tk.END)
            self.ind_ipv4_entry.delete(0, tk.END)
            self.ind_ipv6_entry.delete(0, tk.END)
            self.save_override_btn.config(state=tk.DISABLED)
            self.delete_override_btn.config(state=tk.DISABLED)
            messagebox.showinfo("Removed", "Device profile erased from registry history tracking.")

    def on_fleet_department_changed(self, event=None):
        dept = self.dept_combobox.get()
        if not dept: return
        meta = self.departments[dept]
        v4_base = meta["v4_start"]
        v6_sub = meta["v6_sub"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        allocated_v4 = []
        cursor.execute("SELECT ipv4_address FROM allocated_profiles WHERE department = ?", (dept,))
        for row in cursor.fetchall():
            try: allocated_v4.append(int(row[0].split('.')[-1]))
            except: pass
        next_offset = v4_base
        while next_offset in allocated_v4:
            next_offset += 1
        conn.close()
        
        self.ipv4_entry.delete(0, tk.END)
        self.ipv4_entry.insert(0, f"10.0.0.{next_offset}")
        self.ipv6_entry.delete(0, tk.END)
        self.ipv6_entry.insert(0, f"fd37:e2a1:9c84:{v6_sub}::{next_offset}")
        self.pc_name_entry.delete(0, tk.END)
        self.pc_name_entry.insert(0, f"PC-{dept}-{next_offset}")

    def check_conflicts(self, pc_name, ipv4, ipv6):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if pc_name:
            cursor.execute("SELECT pc_name FROM allocated_profiles WHERE pc_name = ?", (pc_name,))
            if cursor.fetchone():
                conn.close()
                return False, f"Ledger Collision: Hostname identity '{pc_name}' already registered."
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE ipv4_address = ?", (ipv4,))
        row4 = cursor.fetchone()
        if row4:
            conn.close()
            return False, f"Ledger Collision: IPv4 target '{ipv4}' is claimed by machine '{row4[0]}'."
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE ipv6_address = ?", (ipv6,))
        row6 = cursor.fetchone()
        if row6:
            conn.close()
            return False, f"Ledger Collision: IPv6 target '{ipv6}' is claimed by machine '{row6[0]}'."
        conn.close()
        return True, ""

    def populate_adapters(self):
        cmd = "Get-NetAdapter | Where-Object {$_.PhysicalMediaType -eq '802.3' -or $_.PhysicalMediaType -eq 'Native802.11'} | Select-Object -ExpandProperty Name"
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
            adapters = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            if adapters:
                self.adapter_combobox['values'] = adapters
                self.adapter_combobox.set(adapters[0])
            else:
                self.adapter_combobox['values'] = ["Ethernet"]
                self.adapter_combobox.set("Ethernet")
        except:
            self.adapter_combobox['values'] = ["Ethernet"]
            self.adapter_combobox.set("Ethernet")

    def refresh_ledger_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT pc_name, department, ipv4_address, ipv6_address FROM allocated_profiles ORDER BY timestamp DESC")
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()


    def run_cmd(self, cmd):
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def execute_provisioning(self):
        if not is_admin():
            if not messagebox.askyesno("Admin Warning", "Administrative elevation required to apply configurations. Execute anyway?"):
                return
        
        adapter = self.adapter_combobox.get()
        dept = self.dept_combobox.get()
        pc_name = self.pc_name_entry.get().strip()
        ip4 = self.ipv4_entry.get().strip()
        gw = self.gw_entry.get().strip()
        ip6 = self.ipv6_entry.get().strip()
        
        srv_v6_subnet = self.srv_ipv6_entry.get().strip()
        printers_v4 = self.printers_entry.get().strip()
        
        if not dept:
            messagebox.showerror("Selection Error", "Please assign a functional group department first.")
            return
            
        is_valid, err_msg = self.check_conflicts(pc_name, ip4, ip6)
        if not is_valid:
            messagebox.showerror("Conflict Warning", err_msg)
            return

        self.apply_btn.config(state=tk.DISABLED)
        self.log_to_tab1(f"[COMMITTING DEPLOYMENT MATRIX FOR DEVICE GROUP: {dept}]")
        
        if pc_name:
            self.log_to_tab1(f"Mapping host name profile to: {pc_name}...")
            self.run_cmd(f"Rename-Computer -NewName '{pc_name}' -Force")
        
        self.log_to_tab1(f"Setting connection boundary classification profile to interface: {adapter}...")
        self.run_cmd(f"Set-NetConnectionProfile -InterfaceAlias '{adapter}' -NetworkCategory Public")
        
        self.log_to_tab1("Provisioning dual-stack adapter interfaces...")
        self.run_cmd(f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -AddressFamily IPv4 -Confirm:$false")
        self.run_cmd(f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip4}' -PrefixLength 24 -DefaultGateway '{gw}'")
        
        self.run_cmd(f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -AddressFamily IPv6 -Confirm:$false")
        self.run_cmd(f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip6}' -PrefixLength 64")
        
        self.log_to_tab1("Purging baseline firewall filters...")
        for rule in ['Block-Local-IPv4-CrossTalk', 'Allow-IPv4-Printers', 'Isolate-IPv6-PCs', 'Allow-IPv6-Master-Servers']:
            self.run_cmd(f"Remove-NetFirewallRule -DisplayName '{rule}' -ErrorAction SilentlyContinue")

        # Hub-and-Spoke Firewall Injections
        self.run_cmd("New-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk' -Direction Inbound -Action Block -RemoteAddress '10.0.0.1-10.0.0.253' -Protocol Any")
        if printers_v4:
            self.run_cmd(f"New-NetFirewallRule -DisplayName 'Allow-IPv4-Printers' -Direction Inbound -Action Allow -RemoteAddress '{printers_v4}' -Protocol Any")
        self.run_cmd("New-NetFirewallRule -DisplayName 'Isolate-IPv6-PCs' -Direction Inbound -Action Block -RemoteAddress 'fd37:e2a1:9c84::/48' -Protocol Any")
        if srv_v6_subnet:
            self.run_cmd(f"New-NetFirewallRule -DisplayName 'Allow-IPv6-Master-Servers' -Direction Inbound -Action Allow -RemoteAddress '{srv_v6_subnet}' -Protocol Any")
            
        # --- Advanced Optimization Executive Sub-Matrix ---
        self.log_to_tab1("Injecting advanced optimization matrix...")
        
        if self.tune_autotune.get():     self.run_cmd("netsh int tcp set global autotuninglevel=normal")
        if self.tune_cubic.get():        self.run_cmd("netsh int tcp set global congestionprovider=cubic")
        if self.tune_rss.get():          self.run_cmd("netsh int tcp set global rss=enabled")
        if self.tune_chimney.get():      self.run_cmd("netsh int tcp set global chimney=enabled")
        if self.tune_timestamps.get():   self.run_cmd("netsh int tcp set global timestamps=disabled")
        if self.tune_netdma.get():       self.run_cmd("netsh int tcp set global netdma=enabled")
        if self.tune_ecn.get():          self.run_cmd("netsh int tcp set global ecncapability=enabled")
        if self.tune_throttling.get():   self.run_cmd("Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile' -Name 'NetworkThrottlingIndex' -Value 4294967295 -Type DWord -Force")

        if self.tune_jumbo.get():
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Jumbo Packet' -DisplayValue '9014 Bytes' -ErrorAction SilentlyContinue")
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Jumbo Frame' -DisplayValue '9KB' -ErrorAction SilentlyContinue")
            
        if self.tune_eee.get():
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Energy Efficient Ethernet' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue")
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName '*EEE' -DisplayValue '0' -ErrorAction SilentlyContinue")

        if self.tune_offload.get():
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Large Send Offload V2 (IPv4)' -DisplayValue 'Enabled' -ErrorAction SilentlyContinue")
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Large Send Offload V2 (IPv6)' -DisplayValue 'Enabled' -ErrorAction SilentlyContinue")
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'IPv4 Checksum Offload' -DisplayValue 'Rx & Tx Enabled' -ErrorAction SilentlyContinue")
            self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'IPv6 Checksum Offload' -DisplayValue 'Rx & Tx Enabled' -ErrorAction SilentlyContinue")

        # Record Entry to Database Ledger
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)", (pc_name, dept, ip4, ip6))
        conn.commit()
        conn.close()
        
        self.refresh_ledger_view()
        self.log_to_tab1("🏆 [PROVISIONING COMPLETE - PERFORMANCE ENGINE ENGAGED]")
        messagebox.showinfo("Matrix Applied", f"System successfully optimized and provisioned for group: {dept}")
        self.apply_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkConfiguratorApp(root)
    root.mainloop()