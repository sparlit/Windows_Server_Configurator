# Windows Server Configurator - Repository Analysis Report

## Overview
This repository contains a collection of network provisioning, zero-trust security isolation, and file server optimization scripts designed for Windows Server and client environments. The tooling combines Python Tkinter GUI applications and PowerShell automation scripts to streamline workstation setup, IP address allocation, firewall boundary enforcement, and SMB/TCP network performance tuning.

---

## 1. Consolidated Architecture & Main Entry Points

### Primary Tools

1. **`AutoPerformanceTuner.ps1` & `run_autotuner.bat`**
   - **Role**: Flagship Autonomous Windows Performance Tuning Tool with Windows Forms GUI.
   - **Features**:
     - **Auto-Detection**: Scans CPU logical/physical cores, RAM capacity, OS role (Server vs Client), active physical network adapters, and disk drive types.
     - **Auto-Backup**: Automatically exports timestamped `.reg` registry state backups and `.json` metadata snapshots prior to executing any modifications.
     - **Full Auto-Tuning Engine**: Optimizes Power/CPU scheduling, Kernel & Memory allocations, Storage & NTFS file system settings, TCP Network stack & NIC offloading, SMB Multichannel & protocol pipelines, and latency/throttling parameters across 6 core subsystems.
     - **Rollback Capabilities**: Provides a 1-click "Restore State Backup" mechanism to undo tuning changes.

2. **`NetworkConfigurator.py`**
   - **Role**: Multi-tab Python Tkinter GUI application ("Enterprise Zero-Trust Deployment & Tuning Suite").
   - **Features**:
     - **Fleet Provisioning Center**: Assigns departments, static IPv4/IPv6, gateway, drive mappings (`MountDrives.bat`), logs allocations to SQLite (`network_config_history.db`), and applies firewall rules.
     - **Individual Device Config**: Queries, updates, or deletes endpoint records from the database ledger.
     - **Optimization Tuning Suite**: Configures advanced TCP/IP stack parameters, jumbo frames, RSS, EEE suppression, checksum offloads, and SMB multichannel.

3. **`Universal_Server_Tuner.ps1`**
   - **Role**: Windows Forms GUI application ("Context-Aware Autonomous File Server Tuning Engine").
   - **Key Functions**: Context-aware OS auto-detection (Server vs Client), dynamic TCP setting configuration (CUBIC/ECN), SMB credits maxing, MFT zone reservation and lookup cache expansion, and SMB multichannel re-binding.

4. **`winservertune.ps1`**
   - **Role**: CLI-based automatic performance and file server tuning script.
   - **Key Functions**: Detects system RAM and CPU cores, sets high-performance power plan, disables paging executive, enables dynamic TCP auto-tuning, configures CUBIC congestion control, enables RSS and hardware offloading, and disables SMB1 / 8dot3 file name creation.

5. **Specialized Tuners**:
   - `SMB_Tuner.ps1`: Dedicated SMB Multichannel auto-detection and link aggregation tuner.
   - `File_Server_Max_Performance.ps1` & `File_Server_Legacy_Compatible.ps1`: SMB file server performance optimizers.
   - `Server_Ultimate_Tuner.ps1`: Full-server performance audit and throttle-removal utility.

6. **Batch Launchers**:
   - `run_autotuner.bat`: Executes `AutoPerformanceTuner.ps1` with auto-elevation and execution policy bypass.
   - `serveropt.bat`: Executes `Universal_Server_Tuner.ps1` with PowerShell execution policy bypass.
   - `servertune.bat`: Executes `winservertune.ps1` with PowerShell execution policy bypass.

---

## 2. Key Findings & Execution Requirements

1. **Clean Repository Structure**:
   - Redundant numbered versions (`*1.ps1`, `*2.py`, etc.) have been merged into single canonical entry points.
   - Flagship fully automatic performance tuning tool (`AutoPerformanceTuner.ps1` / `run_autotuner.bat`) is provided for automated tuning with built-in backup and restore functionality.

2. **Execution Requirements**:
   - Python GUI and PowerShell scripts require **Administrator Rights** (`Run as Administrator`) on Windows to modify network interface configurations, firewall rules, and Windows Registry (`HKLM`) keys.
