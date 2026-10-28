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
        self.root.title("Unified Network & Firewall Configurator v2")
        self.root.geometry("650x780")
        self.root.resizable(False, False)
        
        # Initialize Database
        self.db_path = "network_config_history.db"
        self.init_database()
        
        # Setup Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Main Layout Frame
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Section 1: Adapter Selection ---
        adapter_group = ttk.LabelFrame(main_frame, text=" 🔌 Network Adapter Selection ", padding="10")
        adapter_group.pack(fill=tk.X, pady=5)
        
        ttk.Label(adapter_group, text="Local Physical Adapter:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.adapter_combobox = ttk.Combobox(adapter_group, width=32, state="readonly")
        self.adapter_combobox.grid(row=0, column=1, padx=5, pady=2)
        
        self.refresh_btn = ttk.Button(adapter_group, text="🔄 Refresh", command=self.populate_adapters, width=10)
        self.refresh_btn.grid(row=0, column=2, padx=5, pady=2)
        
        # --- Section 2: Identity ---
        identity_group = ttk.LabelFrame(main_frame, text=" 🖥️ System Identity ", padding="10")
        identity_group.pack(fill=tk.X, pady=5)
        
        ttk.Label(identity_group, text="New PC Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.pc_name_entry = ttk.Entry(identity_group, width=35)
        self.pc_name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # --- Section 3: IPv4 Network Properties ---
        ipv4_group = ttk.LabelFrame(main_frame, text=" 🌐 IPv4 Adapter Properties (Internet & Printers) ", padding="10")
        ipv4_group.pack(fill=tk.X, pady=5)
        
        ttk.Label(ipv4_group, text="Static IPv4 Address:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.ipv4_entry = ttk.Entry(ipv4_group, width=35)
        self.ipv4_entry.insert(0, "10.0.0.17")
        self.ipv4_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(ipv4_group, text="Subnet Mask:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.mask_entry = ttk.Entry(ipv4_group, width=35)
        self.mask_entry.insert(0, "255.255.255.0")
        self.mask_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(ipv4_group, text="Default Gateway:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.gw_entry = ttk.Entry(ipv4_group, width=35)
        self.gw_entry.insert(0, "10.0.0.254")
        self.gw_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # --- Section 4: IPv6 Network Properties ---
        ipv6_group = ttk.LabelFrame(main_frame, text=" 🔒 IPv6 Adapter Properties (Internal Server Lane) ", padding="10")
        ipv6_group.pack(fill=tk.X, pady=5)
        
        ttk.Label(ipv6_group, text="Static IPv6 Address:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.ipv6_entry = ttk.Entry(ipv6_group, width=35)
        self.ipv6_entry.insert(0, "fd00:1::17")
        self.ipv6_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(ipv6_group, text="IPv6 Prefix Length:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.prefix_entry = ttk.Entry(ipv6_group, width=35)
        self.prefix_entry.insert(0, "64")
        self.prefix_entry.grid(row=1, column=1, padx=5, pady=2)

        # --- Section 5: Dual-Stack Strict Firewall Engine ---
        fw_group = ttk.LabelFrame(main_frame, text=" 🛡️ Segmentation Firewall Policy Architecture ", padding="10")
        fw_group.pack(fill=tk.X, pady=5)
        
        ttk.Label(fw_group, text="Trusted Server IPv6 List (Comma separated):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.srv_ipv6_entry = ttk.Entry(fw_group, width=35)
        self.srv_ipv6_entry.insert(0, "fd00:1::1,fd00:1::3")
        self.srv_ipv6_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(fw_group, text="Trusted Printers IPv4 List (Comma separated):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.printers_entry = ttk.Entry(fw_group, width=35)
        self.printers_entry.insert(0, "10.0.0.200,10.0.0.201")
        self.printers_entry.grid(row=1, column=1, padx=5, pady=2)

        # --- Execution Console ---
        self.log_text = tk.Text(main_frame, height=6, width=80, state=tk.DISABLED, bg="#2b2b2b", fg="#a9b7c6", font=("Consolas", 9))
        self.log_text.pack(pady=5)

        # --- Action Trigger ---
        self.apply_btn = ttk.Button(main_frame, text="🚀 Execute & Provision System Configuration", command=self.execute_provisioning)
        self.apply_btn.pack(fill=tk.X, ipady=3, pady=2)
        
        # Populate initial adapters list
        self.populate_adapters()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS allocated_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pc_name TEXT UNIQUE,
                ipv4_address TEXT UNIQUE,
                ipv6_address TEXT UNIQUE,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def check_conflicts(self, pc_name, ipv4, ipv6):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check hostname duplicate
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE pc_name = ? AND pc_name != ''", (pc_name,))
        if cursor.fetchone():
            conn.close()
            return False, f"Violation: PC Name '{pc_name}' has already been allocated to another endpoint."
            
        # Check IPv4 conflict
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE ipv4_address = ?", (ipv4,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return False, f"Violation: IPv4 Address '{ipv4}' is already registered to '{row[0]}'."
            
        # Check IPv6 conflict
        cursor.execute("SELECT pc_name FROM allocated_profiles WHERE ipv6_address = ?", (ipv6,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return False, f"Violation: IPv6 Address '{ipv6}' is already registered to '{row[0]}'."
            
        conn.close()
        return True, ""

    def log_to_database(self, pc_name, ipv4, ipv6):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO allocated_profiles (pc_name, ipv4_address, ipv6_address)
                VALUES (?, ?, ?)
            """, (pc_name, ipv4, ipv6))
            conn.commit()
            conn.close()
            self.log("💾 Configuration entry recorded successfully in local tracking database.")
        except Exception as e:
            self.log(f"⚠️ Database Log Failure: {str(e)}")

    def populate_adapters(self):
        self.refresh_btn.config(state=tk.DISABLED)
        # PowerShell query filtering down to Up physical network interfaces
        cmd = "Get-NetAdapter | Where-Object {$_.PhysicalMediaType -eq '802.3' -or $_.PhysicalMediaType -eq 'Native802.11'} | Select-Object -ExpandProperty Name"
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
            adapters = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            if adapters:
                self.adapter_combobox['values'] = adapters
                self.adapter_combobox.set(adapters[0])
                self.log(f"Found active physical interfaces: {', '.join(adapters)}")
            else:
                self.adapter_combobox['values'] = ["Ethernet", "Wi-Fi"]
                self.adapter_combobox.set("Ethernet")
                self.log("⚠️ No physical network interfaces auto-detected. Defaulted list.")
        except Exception as e:
            self.adapter_combobox['values'] = ["Ethernet"]
            self.adapter_combobox.set("Ethernet")
            self.log(f"⚠️ Error mapping system adapters: {str(e)}")
        finally:
            self.refresh_btn.config(state=tk.NORMAL)

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "
")
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
            if not messagebox.askyesno("Admin Warning", "Running execution without administrative permissions will fail. Continue anyway?"):
                return
        
        adapter = self.adapter_combobox.get()
        if not adapter:
            messagebox.showerror("Error", "Please select a target network adapter interface.")
            return

        pc_name = self.pc_name_entry.get().strip()
        ip4 = self.ipv4_entry.get().strip()
        mask = self.mask_entry.get().strip()
        gw = self.gw_entry.get().strip()
        ip6 = self.ipv6_entry.get().strip()
        prefix = self.prefix_entry.get().strip()
        srv_v6 = self.srv_ipv6_entry.get().strip()
        printers_v4 = self.printers_entry.get().strip()
        
        # 1. Database Duplication / Allocation Validation Guard
        is_valid, err_msg = self.check_conflicts(pc_name, ip4, ip6)
        if not is_valid:
            messagebox.showerror("Network Allocation Violation", err_msg)
            self.log(f"❌ Execution Blocked: {err_msg}")
            return

        self.apply_btn.config(state=tk.DISABLED)
        self.log("[STARTING SYSTEM PROVISIONING MATRIX]")
        
        # 2. Update Hostname identity
        if pc_name:
            self.log(f"Changing device hostname identity to: {pc_name}...")
            success, out = self.run_cmd(f"Rename-Computer -NewName '{pc_name}' -Force")
            if success:
                self.log("✅ Identity renamed successfully. A reboot will be required later.")
            else:
                self.log(f"❌ Hostname mapping failure: {out.strip()}")
        
        # 3. Network Adapter Resubnetting
        self.log(f"Switching Network Profile to Public for Adapter: {adapter} to silence NetBIOS...")
        self.run_cmd(f"Set-NetConnectionProfile -InterfaceAlias '{adapter}' -NetworkCategory Public")
        
        self.log(f"Binding Static IPv4 Layer: {ip4}...")
        self.run_cmd(f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -AddressFamily IPv4 -Confirm:$false")
        success, out = self.run_cmd(f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip4}' -PrefixLength 24 -DefaultGateway '{gw}'")
        if success: self.log("✅ Static IPv4 Network parameters bound successfully.")
        
        self.log(f"Binding Static Isolation IPv6 Layer: {ip6}...")
        self.run_cmd(f"Remove-NetIPAddress -InterfaceAlias '{adapter}' -AddressFamily IPv6 -Confirm:$false")
        success, out = self.run_cmd(f"New-NetIPAddress -InterfaceAlias '{adapter}' -IPAddress '{ip6}' -PrefixLength {prefix}")
        if success: self.log("✅ Static IPv6 Network parameters bound successfully.")
        
        # 4. Purge existing target firewall segments
        self.log("Purging old custom policy rules...")
        self.run_cmd("Remove-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk' -ErrorAction SilentlyContinue")
        self.run_cmd("Remove-NetFirewallRule -DisplayName 'Allow-IPv4-Printers' -ErrorAction SilentlyContinue")
        self.run_cmd("Remove-NetFirewallRule -DisplayName 'Isolate-IPv6-PCs' -ErrorAction SilentlyContinue")
        self.run_cmd("Remove-NetFirewallRule -DisplayName 'Allow-IPv6-Servers' -ErrorAction SilentlyContinue")

        # 5. Inject Firewall Architectures
        self.log("Deploying Rule: Block-Local-IPv4-CrossTalk...")
        self.run_cmd("New-NetFirewallRule -DisplayName 'Block-Local-IPv4-CrossTalk' -Direction Inbound -Action Block -RemoteAddress '10.0.0.1-10.0.0.253' -Protocol Any")
        
        if printers_v4:
            self.log(f"Injecting Bypass Rule: Allow-IPv4-Printers -> [{printers_v4}]...")
            self.run_cmd(f"New-NetFirewallRule -DisplayName 'Allow-IPv4-Printers' -Direction Inbound -Action Allow -RemoteAddress '{printers_v4}' -Protocol Any")
            
        self.log("Deploying Rule: Isolate-IPv6-PCs...")
        self.run_cmd("New-NetFirewallRule -DisplayName 'Isolate-IPv6-PCs' -Direction Inbound -Action Block -RemoteAddress 'fd00:1::/64' -Protocol Any")
        
        if srv_v6:
            self.log(f"Injecting Bypass Rule: Allow-IPv6-Servers -> [{srv_v6}]...")
            self.run_cmd(f"New-NetFirewallRule -DisplayName 'Allow-IPv6-Servers' -Direction Inbound -Action Allow -RemoteAddress '{srv_v6}' -Protocol Any")
            
        # 6. Success Logging to Shared History
        self.log_to_database(pc_name, ip4, ip6)
        self.log("🏆 [SYSTEM CONFLICT MITIGATION COMPLETE]")
        messagebox.showinfo("Matrix Applied", "Network Provisioning completed successfully and registered to tracking database.")
        self.apply_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkConfiguratorApp(root)
    root.mainloop()
