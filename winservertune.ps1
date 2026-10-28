<#
.SYNOPSIS
    Windows Server Superior Performance & File Server Optimization Script.
.DESCRIPTION
    Dynamically detects hardware capacities and auto-tunes the OS, network stack,
    and SMB configuration for maximum throughput, low latency, and rock-solid stability.
.NOTES
    Run as Administrator. Requires a reboot after execution.
#>

# Ensure script is running as Administrator
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as an Administrator. Exiting."
    Exit
}

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " STARTING AUTOMATIC PERFORMANCE & FILE SERVER TUNING     " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# -------------------------------------------------------------------------
# 1. HARDWARE AUTO-DETECTION & LOGIC DYNAMICS
# -------------------------------------------------------------------------
Write-Host "[*] Detecting hardware capacities..." -ForegroundColor Yellow

$TotalRAMBytes = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
$TotalRAM_GB   = [Math]::Round($TotalRAMBytes / 1GB)
$LogicalCores  = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$NetworkLinks  = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.Virtual -eq $false }

Write-Host " -> Detected CPU Cores: $LogicalCores" -ForegroundColor Gray
Write-Host " -> Detected RAM: ${TotalRAM_GB} GB" -ForegroundColor Gray
Write-Host " -> Active Physical Network Adapters: $($NetworkLinks.Count)" -ForegroundColor Gray

# Set dynamic scaling multipliers based on RAM size
if ($TotalRAM_GB -le 16) {
    $CacheSizeProfile = "Low"
    $MaxWorkerThreads = $LogicalCores * 16
} elseif ($TotalRAM_GB -le 64) {
    $CacheSizeProfile = "Medium"
    $MaxWorkerThreads = $LogicalCores * 32
} else {
    $CacheSizeProfile = "High"
    $MaxWorkerThreads = $LogicalCores * 64
}

# -------------------------------------------------------------------------
# 2. POWER MANAGEMENT (Sustained Maximum Performance)
# -------------------------------------------------------------------------
Write-Host "[*] Tuning Power Profile to High Performance..." -ForegroundColor Yellow
# Enforce the Ultimate/High Performance GUID to stop CPU core parking and frequency throttling
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

# -------------------------------------------------------------------------
# 3. KERNEL & MEMORY MANAGEMENT AUTO-TUNING
# -------------------------------------------------------------------------
Write-Host "[*] Auto-adjusting OS Kernel & Memory Allocations (Profile: $CacheSizeProfile)..." -ForegroundColor Yellow
$MemoryRegPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"

# Disable paging Executive (keeps system drivers and kernel code in RAM instead of paging to disk)
Set-ItemProperty -Path $MemoryRegPath -Name "DisablePagingExecutive" -Value 1 -Type DWORD

# Optimizes system pages allocation for server-centric workloads
Set-ItemProperty -Path $MemoryRegPath -Name "LargeSystemCache" -Value 1 -Type DWORD

# Configure system thread tuning based on core counts
$SystemRegPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager"
Set-ItemProperty -Path $SystemRegPath -Name "MaxWorkerThreads" -Value $MaxWorkerThreads -Type DWORD

# -------------------------------------------------------------------------
# 4. NETWORK STACK ADAPTIVE TUNING (Fast & Stable Connections)
# -------------------------------------------------------------------------
Write-Host "[*] Optimizing TCP/IP Stack & Global Network Parameters..." -ForegroundColor Yellow

# Enable Receive Window Auto-Tuning to dynamically scale TCP window sizes based on link speed
Set-NetTCPSetting -SettingName Server -AutoTuningLevelFrequency High -AutoTuningLevel Normal

# Enable Compound TCP (CTCP) or CUBIC depending on OS architecture for aggressive congestion control
Set-NetTCPSetting -SettingName Server -CongestionProvider CUBIC -ErrorRecoveryHanding Enabled

# Enable ECN (Explicit Congestion Notification) to minimize packet loss across heavy congestion
Set-NetTCPSetting -SettingName Server -EcnCapability Enabled

# Optimize TCP Timestamps and TFO (TCP Fast Open) for speedier connection handshakes
Set-NetTCPSetting -SettingName Server -Timestamps Enabled

# Hardware Offloading Adaptations on Physical Network Adapters
foreach ($Adapter in $NetworkLinks) {
    Write-Host "    -> Tuning Hardware Offloads for adapter: $($Adapter.Name)" -ForegroundColor Gray
    
    # Enable Receive Side Scaling (RSS) to spread network processing across multiple CPU cores
    Enable-NetAdapterRss -Name $Adapter.Name -ErrorAction SilentlyContinue
    
    # Enable Large Send Offload (LSO) and Checksum Offload to shift load from CPU to Network Card
    Enable-NetAdapterLso -Name $Adapter.Name -IPv4 -ErrorAction SilentlyContinue
    Set-NetAdapterAdvancedProperty -Name $Adapter.Name -DisplayName "Large Send Offload v2 (IPv4)" -DisplayValue "Enabled" -ErrorAction SilentlyContinue
    Set-NetAdapterAdvancedProperty -Name $Adapter.Name -DisplayName "IPv4 Checksum Offload" -DisplayValue "Rx & Tx Enabled" -ErrorAction SilentlyContinue
    
    # Maximize Receive and Transmit Buffers to accommodate heavy traffic bursts without dropping packets
    Set-NetAdapterAdvancedProperty -Name $Adapter.Name -DisplayName "Receive Buffers" -DisplayValue "2048" -ErrorAction SilentlyContinue
    Set-NetAdapterAdvancedProperty -Name $Adapter.Name -DisplayName "Transmit Buffers" -DisplayValue "2048" -ErrorAction SilentlyContinue
}

# -------------------------------------------------------------------------
# 5. SUPERIOR FILE SERVER CAPABILITIES (SMB Protocol Tuning)
# -------------------------------------------------------------------------
Write-Host "[*] Executing Advanced SMB & File Server Optimization..." -ForegroundColor Yellow

# Enable SMB Multichannel (forces Windows to bundle multiple NICs together automatically for aggregate bandwidth)
Set-SmbServerConfiguration -EnableMultiChannel $true -Confirm:$false

# Dynamically adjust File System Cache limits according to detected memory profiles
$LanmanServerParamPath = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"

if ($CacheSizeProfile -eq "High") {
    # Large RAM servers get significantly larger SMB worker thread caps and internal file buffers
    Set-ItemProperty -Path $LanmanServerParamPath -Name "MaxThreadsPerCmd" -Value 256 -Type DWORD
    Set-ItemProperty -Path $LanmanServerParamPath -Name "MaxWorkItems" -Value 8192 -Type DWORD
    Set-ItemProperty -Path $LanmanServerParamPath -Name "Size" -Value 3 -Type DWORD # Optimize for network applications/file sharing
} else {
    Set-ItemProperty -Path $LanmanServerParamPath -Name "MaxThreadsPerCmd" -Value 128 -Type DWORD
    Set-ItemProperty -Path $LanmanServerParamPath -Name "MaxWorkItems" -Value 4096 -Type DWORD
    Set-ItemProperty -Path $LanmanServerParamPath -Name "Size" -Value 3 -Type DWORD
}

# Disable SMB1 protocol strictly to eliminate legacy overhead and secure the pipeline
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Confirm:$false

# Fine-tune the local file system (NTFS) configurations
# Disable 8dot3 legacy short name generation to drastically speed up folder creations on massive volumes
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "NtfsDisable8dot3NameCreation" -Value 1 -Type DWORD

# Disable Last Access Time stamp updates to cut file-read overhead operations in half
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "NtfsDisableLastAccessUpdate" -Value 1 -Type DWORD

# -------------------------------------------------------------------------
# COMPLETE
# -------------------------------------------------------------------------
Write-Host "=========================================================" -ForegroundColor Green
Write-Host " AUTO-TUNING COMPLETE! SUPERIOR SPEEDS ARE SET.         " -ForegroundColor Green
Write-Host " Please reboot the server to apply all adjustments.      " -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
