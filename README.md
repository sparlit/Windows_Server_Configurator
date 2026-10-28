# Windows Server Configurator

An enterprise suite of Python and PowerShell automation tools designed for Windows workstation fleet provisioning, zero-trust network isolation, and file server performance tuning.

---

## Tool Overview

### 1. Autonomous Performance & Tuning Engine (`AutoPerformanceTuner.ps1` & `run_autotuner.bat`)
A standalone, fully automated Windows Forms GUI application for end-to-end performance tuning across Windows client and server environments:
- **Auto-Detection**: Queries OS architecture, total physical RAM, logical/physical CPU cores, active physical network adapters, and physical disk media types.
- **Auto-Backup**: Exports a timestamped `.reg` registry state backup and JSON metadata snapshot into a `Backups` directory prior to modifying system parameters.
- **Auto-Tuning Engine (6 Subsystems)**:
  1. *Power & CPU*: Sets Ultimate/High Performance power plan, unparks CPU cores, and disables frequency throttling.
  2. *Kernel & Memory*: Disables paging executive (`DisablePagingExecutive=1`), activates Large System Cache, expands worker thread pools dynamically based on RAM capacity, and optimizes NTFS memory usage.
  3. *Storage & NTFS FileSystem*: Disables 8dot3 short name creation, disables last access time updates, expands MFT Zone reservations, and enforces TRIM / delete notification for SSDs.
  4. *Network TCP Stack & Hardware Offloading*: Configures dynamic TCP congestion providers (CUBIC/CTCP), ECN capability, Receive Window Auto-Tuning, RSS, LSO v2, Checksum Offloading, expands Receive/Transmit buffers (2048), and disables Energy Efficient Ethernet (EEE) latency spikes.
  5. *SMB Protocol Pipelining*: Enables SMB Multichannel, maxes out SMB2 credit pools (`Smb2CreditsMax`), expands LanmanServer work item limits, and disables legacy SMB1.
  6. *System Latency & Throttling Removal*: Removes network throttling (`NetworkThrottlingIndex=0xFFFFFFFF`), maximizes system responsiveness for active tasks, expands dynamic ephemeral port ranges (`MaxUserPort=65534`), and reduces TCP timed wait delay.
- **Rollback Feature**: Built-in 1-click restore button to re-import pre-tuning registry backups if needed.

### 2. Network Provisioning & Zero-Trust Security (`NetworkConfigurator.py`)
A feature-rich multi-tab Tkinter GUI application for workstation deployment and tracking (`network_config_history.db`):
- **Fleet Provisioning Center**: Assigns functional departments, static IPv4 & IPv6 addresses, gateway settings, auto-mounts drive shares (`MountDrives.bat`), and records profiles in an SQLite database ledger.
- **Individual Device Config**: Queries, updates, or purges endpoint records from the tracking ledger.
- **Optimization Tuning Suite**: Applies advanced network stack optimizations (TCP dynamic auto-tuning, jumbo frames, Receive-Side Scaling, EEE suppression, checksum offloads, and SMB multichannel).

### 3. Autonomous File Server Tuning (`Universal_Server_Tuner.ps1` & `winservertune.ps1`)
PowerShell utilities for tuning Windows Server kernel, memory, and TCP/IP stack:
- **`Universal_Server_Tuner.ps1`**: A context-aware Windows Forms GUI tool that detects OS capabilities (Server vs. Client), configures dynamic TCP congestion providers (CUBIC/ECN), maxes out SMB2 credit pools, and expands lookup cache allocations.
- **`winservertune.ps1`**: A CLI auto-tuner for unattended server optimization.

### 4. Specialized Performance Tuners
- **`SMB_Tuner.ps1`**: GUI tool for SMB Multichannel auto-detection and link aggregation.
- **`File_Server_Max_Performance.ps1` / `File_Server_Legacy_Compatible.ps1`**: SMB file server performance optimizers.
- **`Server_Ultimate_Tuner.ps1`**: Full server performance audit and throttle-removal utility.

### 5. Batch Launchers
- **`run_autotuner.bat`**: Runs `AutoPerformanceTuner.ps1` with Administrator elevation and PowerShell execution policy bypass.
- **`serveropt.bat`**: Runs `Universal_Server_Tuner.ps1` with PowerShell execution policy bypass.
- **`servertune.bat`**: Runs `winservertune.ps1` with PowerShell execution policy bypass.

---

## System Requirements & Prerequisites
- Operating System: Windows 10/11 or Windows Server 2016+
- Execution Privileges: **Administrator Rights** are required to modify network interface properties, firewall rules, and Windows Registry (`HKLM`) keys.
- Python 3.x with Tkinter (for `NetworkConfigurator.py`).
