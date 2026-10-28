import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import ctypes
import sqlite3
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class NetworkConfiguratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Absolute Zero-Trust Network & Performance Engine")
        self.root.geometry("780x900")
        self.root.resizable(False, False)
        
        self.db_path = "network_config_history.db"
        self.init_database()
        
        # Department Mapping Configurations
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
        
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Section 1: Adapter & Department Selection ---
        top_group = ttk.LabelFrame(main_frame, text=" 🔌 Core Allocation Controls ", padding="10")
        top_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(top_group, text="Target Interface:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.adapter_combobox = ttk.Combobox(top_group, width=25, state="readonly")
        self.adapter_combobox.grid(row=0, column=1, padx=5, pady=2)
        
        self.refresh_btn = ttk.Button(top_group, text="🔄 Refresh", command=self.populate_adapters, width=10)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Label(top_group, text="Department / Group:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.dept_combobox = ttk.Combobox(top_group, values=list(self.departments.keys()), width=25, state="readonly")
        self.dept_combobox.grid(row=1, column=1, padx=5, pady=2)
        self.dept_combobox.bind("<<ComboboxSelected>>", self.auto_suggest_ips)
        
        # --- Section 2: Identity & IPv4 ---
        network_group = ttk.LabelFrame(main_frame, text=" 🌐 Endpoint Identity & IPv4 Properties (Internet Hub) ", padding="10")
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
        
        # --- Section 3: Isolated IPv6 Lane ---
        ipv6_group = ttk.LabelFrame(main_frame, text=" 🔒 Isolated Service IPv6 Properties (Strict Server Link) ", padding="10")
        ipv6_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(ipv6_group, text="Static IPv6 Address:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.ipv6_entry = ttk.Entry(ipv6_group, width=35)
        self.ipv6_entry.grid(row=0, column=1, padx=5, pady=2)

        # --- Section 4: Security Boundaries ---
        fw_group = ttk.LabelFrame(main_frame, text=" 🛡️ Security Boundary Configurations ", padding="10")
        fw_group.pack(fill=tk.X, pady=4)
        
        ttk.Label(fw_group, text="Master Server Subnet Target:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.srv_ipv6_entry = ttk.Entry(fw_group, width=35)
        self.srv_ipv6_entry.insert(0, "fd37:e2a1:9c84:1000::/64")
        self.srv_ipv6_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(fw_group, text="Trusted Hardware Printers IPv4:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.printers_entry = ttk.Entry(fw_group, width=35)
        self.printers_entry.insert(0, "10.0.0.200,10.0.0.201")
        self.printers_entry.grid(row=1, column=1, padx=5, pady=2)

        # --- Section 5: Allocation Ledger ---
        ledger_group = ttk.LabelFrame(main_frame, text=" 📊 Enterprise Network Allocation Ledger ", padding="5")
        ledger_group.pack(fill=tk.BOTH, expand=True, pady=4)
        
        self.tree = ttk.Treeview(ledger_group, columns=("PC Name", "Department", "IPv4", "IPv6"), show="headings", height=4)
        self.tree.heading("PC Name", text="PC Name")
        self.tree.heading("Department", text="Department")
        self.tree.heading("IPv4", text="IPv4 Address")
        self.tree.heading("IPv6", text="IPv6 Address")
        self.tree.column("PC Name", width=120)
        self.tree.column("Department", width=130)
        self.tree.column("IPv4", width=120)
        self.tree.column("IPv6", width=220)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Output Terminal Log
        self.log_text = tk.Text(main_frame, height=4, width=85, state=tk.DISABLED, bg="#2b2b2b", fg="#a9b7c6", font=("Consolas", 9))
        self.log_text.pack(pady=4)

        # Apply Configuration Action Button
        self.apply_btn = ttk.Button(main_frame, text="🚀 Apply Absolute Peer Isolation & Full Hardware Optimization", command=self.execute_provisioning)
        self.apply_btn.pack(fill=tk.X, ipady=4)
        
        self.populate_adapters()
        self.refresh_ledger_view()

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

    def refresh_ledger_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT pc_name, department, ipv4_address, ipv6_address FROM allocated_profiles ORDER BY timestamp DESC")
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def auto_suggest_ips(self, event=None):
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
            try: allocated_v4.append(int(row.split('.')[-1]))
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
                return False, f"Ledger Collision: Hostname identity '{pc_name}' has already been registered."
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE ipv4_address = ?", (ipv4,))
        row4 = cursor.fetchone()
        if row4:
            conn.close()
            return False, f"Ledger Collision: IPv4 target '{ipv4}' is claimed by machine '{row4}'."
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE ipv6_address = ?", (ipv6,))
        row6 = cursor.fetchone()
        if row6:
            conn.close()
            return False, f"Ledger Collision: IPv6 target '{ipv6}' is claimed by machine '{row6}'."
        conn.close()
        return True, ""

    def populate_adapters(self):
        cmd = "Get-NetAdapter | Where-Object {$_.PhysicalMediaType -eq '802.3' -or $_.PhysicalMediaType -eq 'Native802.11'} | Select-Object -ExpandProperty Name"
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
            adapters = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            if adapters:
                self.adapter_combobox['values'] = adapters
                self.adapter_combobox.set(adapters)
            else:
                self.adapter_combobox['values'] = ["Ethernet"]
                self.adapter_combobox.set("Ethernet")
        except:
            self.adapter_combobox['values'] = ["Ethernet"]
            self.adapter_combobox.set("Ethernet")

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def run_cmd(self, cmd):
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def execute_provisioning(self):
        if not is_admin():
            if not messagebox.askyesno("Admin Warning", "Administrative elevation missing. Execute anyway?"):
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
            messagebox.showerror("Error", "Please select a functional group department assignment first.")
            return
            
        is_valid, err_msg = self.check_conflicts(pc_name, ip4, ip6)
        if not is_valid:
            messagebox.showerror("Conflict Warning", err_msg)
            return

        self.apply_btn.config(state=tk.DISABLED)
        self.log(f"[DEPLOYING ZERO-TRUST ABSOLUTE ISOLATION FOR GROUP: {dept}]")
        
        if pc_name:
            self.log(f"Mapping host name profile to: {pc_name}...")
            self.run_cmd(f"Rename-Computer -NewName '{pc_name}' -Force")
        
        self.log(f"Setting public binding classification profile to interface: {adapter}...")
        self.run_cmd(f"Set-NetConnectionProfile -InterfaceAlias '{adapter}' -NetworkCategory Public")
        
        self.log("Provisioning local adapter structural interfaces...")
        self.run_cmd(f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -AddressFamily IPv4 -Confirm:$false")
        self.run_cmd(f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip4}' -PrefixLength 24 -DefaultGateway '{gw}'")
        
        self.log("Applying isolated local server lane architecture layer...")
        self.run_cmd(f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -AddressFamily IPv6 -Confirm:$false")
        self.run_cmd(f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip6}' -PrefixLength 64")
        
        self.log("Purging conflicting baseline firewall filters...")
        for rule in ['Block-Local-IPv4-CrossTalk', 'Allow-IPv4-Printers', 'Isolate-IPv6-PCs', 'Allow-IPv6-Master-Servers']:
            self.run_cmd(f"Remove-NetFirewallRule -DisplayName '{rule}' -ErrorAction SilentlyContinue")

        # --- Injected Absolute Zero-Trust Firewall Policy ---
        self.log("Locking down absolute peer-to-peer boundaries...")
        self.run_cmd("New-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk' -Direction Inbound -Action Block -RemoteAddress '10.0.0.1-10.0.0.253' -Protocol Any")
        if printers_v4:
            self.run_cmd(f"New-NetFirewallRule -DisplayName 'Allow-IPv4-Printers' -Direction Inbound -Action Allow -RemoteAddress '{printers_v4}' -Protocol Any")
            
        self.run_cmd("New-NetFirewallRule -DisplayName 'Isolate-IPv6-PCs' -Direction Inbound -Action Block -RemoteAddress 'fd37:e2a1:9c84::/48' -Protocol Any")
        if srv_v6_subnet:
            self.log(f"Carving out exclusive access tunnel to Master Servers: [{srv_v6_subnet}]")
            self.run_cmd(f"New-NetFirewallRule -DisplayName 'Allow-IPv6-Master-Servers' -Direction Inbound -Action Allow -RemoteAddress '{srv_v6_subnet}' -Protocol Any")
            
        # --- Kernel & Hardware Network Performance Tuning Engine ---
        self.log("Optimizing TCP/IP stack configuration parameters...")
        self.run_cmd("netsh int tcp set global autotuninglevel=normal")
        self.run_cmd("netsh int tcp set global chimney=enabled")
        self.run_cmd("netsh int tcp set global dca=enabled")
        self.run_cmd("netsh int tcp set global netdma=enabled")
        self.run_cmd("netsh int tcp set global congestionprovider=cubic")
        self.run_cmd("netsh int tcp set global timestamps=disabled")
        
        self.log("⚙️ Allocating Hardware NIC Jumbo Packet (MTU 9000) overrides...")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Jumbo Packet' -DisplayValue '9014 Bytes' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Jumbo Frame' -DisplayValue '9KB' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Jumbo Packet' -DisplayValue '9014' -ErrorAction SilentlyContinue")

        self.log("🛑 Suppressing hardware link power savings and throttling thresholds...")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Energy Efficient Ethernet' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Green Ethernet' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Ultra Low Power Mode' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Power Saving Mode' -DisplayValue 'Disabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName '*EEE' -DisplayValue '0' -ErrorAction SilentlyContinue")

        self.log("⚡ Tuning hardware interface offloading configurations...")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Interrupt Moderation' -DisplayValue 'Enabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Large Send Offload V2 (IPv4)' -DisplayValue 'Enabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'Large Send Offload V2 (IPv6)' -DisplayValue 'Enabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'IPv4 Checksum Offload' -DisplayValue 'Rx & Tx Enabled' -ErrorAction SilentlyContinue")
        self.run_cmd(f"Set-NetAdapterAdvancedProperty -Name '{adapter}' -DisplayName 'IPv6 Checksum Offload' -DisplayValue 'Rx & Tx Enabled' -ErrorAction SilentlyContinue")
        
        self.run_cmd("Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile' -Name 'NetworkThrottlingIndex' -Value 4294967295 -Type DWord -Force")
        self.run_cmd("Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile' -Name 'SystemResponsiveness' -Value 0 -Type DWord -Force")

        # Record to tracking ledger
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO allocated_profiles (pc_name, department, ipv4_address, ipv6_address) VALUES (?, ?, ?, ?)", (pc_name, dept, ip4, ip6))
        conn.commit()
        conn.close()
        
        self.refresh_ledger_view()
        self.log("🏆 [PROVISIONING COMPLETE - ABSOLUTE PEER ISOLATION ENFORCED]")
        messagebox.showinfo("Absolute Security Matrix Applied", f"System successfully provisioned for '{dept}'. Client-to-client communication blocked.")
        self.apply_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkConfiguratorApp(root)
    root.mainloop()
