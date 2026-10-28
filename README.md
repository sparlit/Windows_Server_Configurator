# Windows Server Configurator

An enterprise suite of Python and PowerShell automation tools designed for Windows workstation fleet provisioning, zero-trust network isolation, and file server performance tuning.

---

## Tool Overview

### 1. Network Provisioning & Zero-Trust Security (`NetworkConfigurator.py`)
A feature-rich multi-tab Tkinter GUI application for workstation deployment and tracking (`network_config_history.db`):
- **Fleet Provisioning Center**: Assigns functional departments, static IPv4 & IPv6 addresses, gateway settings, auto-mounts drive shares (`MountDrives.bat`), and records profiles in an SQLite database ledger.
- **Individual Device Config**: Queries, updates, or purges endpoint records from the tracking ledger.
- **Optimization Tuning Suite**: Applies advanced network stack optimizations (TCP dynamic auto-tuning, jumbo frames, Receive-Side Scaling, EEE suppression, checksum offloads, and SMB multichannel).

### 2. Autonomous File Server Tuning (`Universal_Server_Tuner.ps1` & `winservertune.ps1`)
PowerShell utilities for tuning Windows Server kernel, memory, and TCP/IP stack:
- **`Universal_Server_Tuner.ps1`**: A context-aware Windows Forms GUI tool that detects OS capabilities (Server vs. Client), configures dynamic TCP congestion providers (CUBIC/ECN), maxes out SMB2 credit pools, and expands lookup cache allocations.
- **`winservertune.ps1`**: A CLI auto-tuner for unattended server optimization.

### 3. Specialized Performance Tuners
- **`SMB_Tuner.ps1`**: GUI tool for SMB Multichannel auto-detection and link aggregation.
- **`File_Server_Max_Performance.ps1` / `File_Server_Legacy_Compatible.ps1`**: SMB file server performance optimizers.
- **`Server_Ultimate_Tuner.ps1`**: Full server performance audit and throttle-removal utility.

### 4. Batch Launchers
- **`serveropt.bat`**: Runs `Universal_Server_Tuner.ps1` with PowerShell execution policy bypass.
- **`servertune.bat`**: Runs `winservertune.ps1` with PowerShell execution policy bypass.

---

## System Requirements & Prerequisites
- Operating System: Windows 10/11 or Windows Server 2016+
- Execution Privileges: **Administrator Rights** are required to modify network interface properties, firewall rules, and Windows Registry (`HKLM`) keys.
- Python 3.x with Tkinter (for `NetworkConfigurator.py`).
