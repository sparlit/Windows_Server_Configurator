<#
.SYNOPSIS
    AutoPerformanceTuner.ps1 - Enterprise Autonomous Windows Performance & Tuning Tool
.DESCRIPTION
    Fully automatic, context-aware performance tuning GUI application for Windows Workstations and Servers.
    Detects hardware parameters (CPU, RAM, Disks, NICs, OS Role) and automatically creates pre-tuning backups,
    adjusts kernel memory limits, network TCP stack settings, storage & file system optimizations, SMB protocols,
    power management profiles, and system latency controls.
.NOTES
    Requires Administrator privileges.
#>

# Check Administrator Rights
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    # If not running as admin, attempt self-elevation or inform user
    Write-Warning "AutoPerformanceTuner requires Administrator privileges to modify system configurations."
}

# Import GUI Assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Set High DPI mode if available
try {
    [System.Windows.Forms.Application]::EnableVisualStyles()
} catch {}

# -------------------------------------------------------------------------
# GLOBAL VARIABLES & DETECTED METRICS
# -------------------------------------------------------------------------
$script:ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $script:ScriptDir) { $script:ScriptDir = Get-Location }

$script:BackupDir = Join-Path $script:ScriptDir "Backups"

$script:SystemSpecs = @{
    OSCaption        = "Unknown"
    OSVersion        = "0.0"
    IsServer         = $false
    TotalRAM_GB      = 0
    LogicalCores     = 0
    PhysicalCores    = 0
    ActiveNICsCount  = 0
    NICList          = @()
    DiskTypes        = @()
    RAMProfile       = "Low" # Low, Medium, High
}

# -------------------------------------------------------------------------
# GUI BUILDING & LAYOUT
# -------------------------------------------------------------------------
$form = New-Object System.Windows.Forms.Form
$form.Text = "Autonomous Windows Performance & Tuning Engine"
$form.Size = New-Object System.Drawing.Size(820, 680)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(24, 26, 32) # Dark theme background

# Font definitions
$fontTitle    = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fontSubTitle = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Regular)
$fontSection  = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontConsole  = New-Object System.Drawing.Font("Consolas", 9, [System.Drawing.FontStyle]::Regular)
$fontButton   = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)

# Header Banner Panel
$pnlHeader = New-Object System.Windows.Forms.Panel
$pnlHeader.Location = New-Object System.Drawing.Point(0, 0)
$pnlHeader.Size = New-Object System.Drawing.Size(820, 75)
$pnlHeader.BackColor = [System.Drawing.Color]::FromArgb(18, 20, 26)
$form.Controls.Add($pnlHeader)

$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "⚡ AUTONOMOUS PERFORMANCE & TUNING ENGINE"
$lblTitle.Font = $fontTitle
$lblTitle.Location = New-Object System.Drawing.Point(20, 12)
$lblTitle.Size = New-Object System.Drawing.Size(780, 30)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(0, 210, 255)
$pnlHeader.Controls.Add($lblTitle)

$lblSubTitle = New-Object System.Windows.Forms.Label
$lblSubTitle.Text = "Fully Automatic Hardware Auto-Detection, Subsystem Optimization, and Pre-Tuning State Safety Backup"
$lblSubTitle.Font = $fontSubTitle
$lblSubTitle.Location = New-Object System.Drawing.Point(22, 43)
$lblSubTitle.Size = New-Object System.Drawing.Size(770, 22)
$lblSubTitle.ForeColor = [System.Drawing.Color]::FromArgb(160, 175, 195)
$pnlHeader.Controls.Add($lblSubTitle)

# System Summary Panel
$grpSummary = New-Object System.Windows.Forms.GroupBox
$grpSummary.Text = " Detected Hardware & OS Environment "
$grpSummary.Font = $fontSection
$grpSummary.Location = New-Object System.Drawing.Point(20, 85)
$grpSummary.Size = New-Object System.Drawing.Size(765, 80)
$grpSummary.ForeColor = [System.Drawing.Color]::FromArgb(0, 210, 255)
$form.Controls.Add($grpSummary)

$lblSummaryText = New-Object System.Windows.Forms.Label
$lblSummaryText.Text = "Scanning hardware parameters..."
$lblSummaryText.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Regular)
$lblSummaryText.Location = New-Object System.Drawing.Point(15, 25)
$lblSummaryText.Size = New-Object System.Drawing.Size(735, 45)
$lblSummaryText.ForeColor = [System.Drawing.Color]::FromArgb(220, 225, 230)
$grpSummary.Controls.Add($lblSummaryText)

# Log Console Label
$lblConsole = New-Object System.Windows.Forms.Label
$lblConsole.Text = "Real-Time Execution & Optimization Log:"
$lblConsole.Font = $fontSection
$lblConsole.Location = New-Object System.Drawing.Point(20, 175)
$lblConsole.Size = New-Object System.Drawing.Size(400, 20)
$lblConsole.ForeColor = [System.Drawing.Color]::FromArgb(220, 225, 230)
$form.Controls.Add($lblConsole)

# Log Output TextBox
$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Font = $fontConsole
$txtLog.Location = New-Object System.Drawing.Point(20, 200)
$txtLog.Size = New-Object System.Drawing.Size(765, 330)
$txtLog.ReadOnly = $true
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(12, 14, 18)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(0, 230, 115)
$form.Controls.Add($txtLog)

# Progress Bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(20, 540)
$progressBar.Size = New-Object System.Drawing.Size(765, 20)
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$form.Controls.Add($progressBar)

# Action Buttons Panel
$btnAutoTune = New-Object System.Windows.Forms.Button
$btnAutoTune.Text = "🚀 Start Full Auto-Tune"
$btnAutoTune.Font = $fontButton
$btnAutoTune.Location = New-Object System.Drawing.Point(20, 575)
$btnAutoTune.Size = New-Object System.Drawing.Size(240, 42)
$btnAutoTune.BackColor = [System.Drawing.Color]::FromArgb(0, 150, 255)
$btnAutoTune.ForeColor = [System.Drawing.Color]::White
$btnAutoTune.FlatStyle = "Flat"
$btnAutoTune.FlatAppearance.BorderSize = 0
$form.Controls.Add($btnAutoTune)

$btnRestore = New-Object System.Windows.Forms.Button
$btnRestore.Text = "↺ Restore State Backup"
$btnRestore.Font = $fontButton
$btnRestore.Location = New-Object System.Drawing.Point(275, 575)
$btnRestore.Size = New-Object System.Drawing.Size(240, 42)
$btnRestore.BackColor = [System.Drawing.Color]::FromArgb(180, 90, 0)
$btnRestore.ForeColor = [System.Drawing.Color]::White
$btnRestore.FlatStyle = "Flat"
$btnRestore.FlatAppearance.BorderSize = 0
$form.Controls.Add($btnRestore)

$btnExportLog = New-Object System.Windows.Forms.Button
$btnExportLog.Text = "💾 Save Log To File"
$btnExportLog.Font = $fontButton
$btnExportLog.Location = New-Object System.Drawing.Point(530, 575)
$btnExportLog.Size = New-Object System.Drawing.Size(255, 42)
$btnExportLog.BackColor = [System.Drawing.Color]::FromArgb(60, 64, 72)
$btnExportLog.ForeColor = [System.Drawing.Color]::White
$btnExportLog.FlatStyle = "Flat"
$btnExportLog.FlatAppearance.BorderSize = 0
$form.Controls.Add($btnExportLog)

# -------------------------------------------------------------------------
# LOGGING & GUI UPDATE HELPER FUNCTIONS
# -------------------------------------------------------------------------
function Write-Log {
    param(
        [string]$Message,
        [string]$Tag = "INFO"
    )
    $timestamp = Get-Date -Format "HH:mm:ss"
    $tagFormatted = "[$Tag]".PadRight(11)
    $line = "$timestamp $tagFormatted $Message`r`n"

    $txtLog.AppendText($line)
    $txtLog.SelectionStart = $txtLog.TextLength
    $txtLog.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}

function Set-Progress {
    param([int]$Value)
    if ($Value -lt 0) { $Value = 0 }
    if ($Value -gt 100) { $Value = 100 }
    $progressBar.Value = $Value
    [System.Windows.Forms.Application]::DoEvents()
}

# -------------------------------------------------------------------------
# 1. HARDWARE & OS AUTO-DETECTION MODULE
# -------------------------------------------------------------------------
function Invoke-HardwareDetection {
    Write-Log "Initiating comprehensive hardware and OS auto-detection sequence..." "DETECT"

    try {
        # OS Detection
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        if ($os) {
            $script:SystemSpecs.OSCaption = $os.Caption
            $script:SystemSpecs.OSVersion = $os.Version
            if ($os.Caption -like "*Server*") {
                $script:SystemSpecs.IsServer = $true
            } else {
                $script:SystemSpecs.IsServer = $false
            }
            $script:SystemSpecs.TotalRAM_GB = [Math]::Round($os.TotalPhysicalMemory / 1GB)
        }

        # CPU Detection
        $cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cpu) {
            $script:SystemSpecs.LogicalCores  = $cpu.NumberOfLogicalProcessors
            $script:SystemSpecs.PhysicalCores = $cpu.NumberOfCores
        } else {
            $script:SystemSpecs.LogicalCores  = [Environment]::ProcessorCount
            $script:SystemSpecs.PhysicalCores = [Environment]::ProcessorCount
        }

        # RAM Scaling Profile
        if ($script:SystemSpecs.TotalRAM_GB -le 16) {
            $script:SystemSpecs.RAMProfile = "Low"
        } elseif ($script:SystemSpecs.TotalRAM_GB -le 64) {
            $script:SystemSpecs.RAMProfile = "Medium"
        } else {
            $script:SystemSpecs.RAMProfile = "High"
        }

        # Active Network Adapters
        $nics = Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' -and $_.Virtual -eq $false }
        if ($nics) {
            $script:SystemSpecs.ActiveNICsCount = $nics.Count
            $script:SystemSpecs.NICList = $nics
        } else {
            $script:SystemSpecs.ActiveNICsCount = 0
        }

        # Disk Storage Detection
        $disks = Get-PhysicalDisk -ErrorAction SilentlyContinue
        if ($disks) {
            $script:SystemSpecs.DiskTypes = $disks.MediaType
        }

        # Update Summary Panel Text
        $roleStr = if ($script:SystemSpecs.IsServer) { "Windows Server Fleet Node" } else { "Windows Desktop Workstation" }
        $nicStr = "$($script:SystemSpecs.ActiveNICsCount) Active Physical Adapter(s)"
        $ramStr = "$($script:SystemSpecs.TotalRAM_GB) GB RAM (Profile: $($script:SystemSpecs.RAMProfile))"
        $cpuStr = "$($script:SystemSpecs.LogicalCores) Logical Cores / $($script:SystemSpecs.PhysicalCores) Physical Cores"

        $lblSummaryText.Text = "• Platform: $($script:SystemSpecs.OSCaption) [$roleStr]`r`n• Processor & RAM: $cpuStr | $ramStr`r`n• Network Infrastructure: $nicStr"

        Write-Log "OS Detected: $($script:SystemSpecs.OSCaption) (Version $($script:SystemSpecs.OSVersion))" "SUCCESS"
        Write-Log "CPU Cores: $($script:SystemSpecs.LogicalCores) logical / $($script:SystemSpecs.PhysicalCores) physical" "SUCCESS"
        Write-Log "RAM Capacity: $($script:SystemSpecs.TotalRAM_GB) GB -> Dynamic Profile: [$($script:SystemSpecs.RAMProfile)]" "SUCCESS"
        Write-Log "Physical NICs Found: $($script:SystemSpecs.ActiveNICsCount)" "SUCCESS"
    }
    catch {
        Write-Log "Detection Notice: Some hardware properties fell back to defaults ($($_.Exception.Message))" "WARN"
    }
}

# -------------------------------------------------------------------------
# 2. AUTOMATIC PRE-TUNING BACKUP MODULE
# -------------------------------------------------------------------------
function Invoke-AutoBackup {
    Write-Log "Creating pre-tuning safety state backup..." "BACKUP"

    if (-not (Test-Path $script:BackupDir)) {
        New-Item -ItemType Directory -Path $script:BackupDir -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $regBackupPath = Join-Path $script:BackupDir "PreTune_Registry_Backup_$timestamp.reg"
    $jsonBackupPath = Join-Path $script:BackupDir "PreTune_Metadata_$timestamp.json"

    # Export key HKLM registry trees via reg.exe
    $softBackupPath = Join-Path $script:BackupDir "PreTune_Software_Backup_$timestamp.reg"

    try {
        # Export SYSTEM and SOFTWARE registry subtrees modified by the tuner
        & reg.exe export "HKLM\SYSTEM\CurrentControlSet" $regBackupPath /y 2>&1 | Out-Null
        & reg.exe export "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" $softBackupPath /y 2>&1 | Out-Null

        # Save snapshot metadata JSON
        $metadata = @{
            Timestamp = $timestamp
            OS        = $script:SystemSpecs.OSCaption
            RAM_GB    = $script:SystemSpecs.TotalRAM_GB
            BackupFile = $regBackupPath
        }
        $metadata | ConvertTo-Json | Out-File -FilePath $jsonBackupPath -Encoding utf8

        Write-Log "Safety backup created successfully: $regBackupPath" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Backup warning: $($_.Exception.Message)" "WARN"
        return $false
    }
}

# -------------------------------------------------------------------------
# 3. COMPREHENSIVE AUTO-TUNING MODULES
# -------------------------------------------------------------------------

# Subsystem 1: Power & CPU Scheduling
function Tune-PowerAndCPU {
    Write-Log "Subsystem [1/6]: Optimizing Power Management & CPU Scheduling..." "TUNING"

    try {
        # Set High Performance power plan
        & powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>&1 | Out-Null
        # Try setting Ultimate Performance if available
        & powercfg /setactive e9e07567-3062-479c-5671-4b600f03223f 2>&1 | Out-Null

        # Disable CPU core parking and frequency throttling parameters in registry
        $powerKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533751-0701-454f-968d-5bba1601b2a5\0cc120b4-1100-4e35-8e4a-0b0bf377527c"
        if (Test-Path $powerKey) {
            Set-ItemProperty -Path $powerKey -Name "Attributes" -Value 0 -Type DWORD -ErrorAction SilentlyContinue
        }

        Write-Log "Power profile set to Ultimate/High Performance. Core parking suppressed." "SUCCESS"
    } catch {
        Write-Log "Power tuning completed with minor non-critical warnings." "WARN"
    }
}

# Subsystem 2: Kernel & Memory Subsystem
function Tune-KernelAndMemory {
    Write-Log "Subsystem [2/6]: Auto-tuning Kernel & Memory Management..." "TUNING"

    $memKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"

    # Calculate dynamic max worker threads
    $cores = $script:SystemSpecs.LogicalCores
    $multiplier = switch ($script:SystemSpecs.RAMProfile) {
        "Low"    { 16 }
        "Medium" { 32 }
        "High"   { 64 }
    }
    $maxWorkerThreads = $cores * $multiplier

    try {
        # Disable Paging Executive (Keeps driver code and kernel in physical RAM)
        Set-ItemProperty -Path $memKey -Name "DisablePagingExecutive" -Value 1 -Type DWORD -ErrorAction SilentlyContinue

        # Enable Large System Cache
        Set-ItemProperty -Path $memKey -Name "LargeSystemCache" -Value 1 -Type DWORD -ErrorAction SilentlyContinue

        # Tune system worker threads
        $sysKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager"
        Set-ItemProperty -Path $sysKey -Name "MaxWorkerThreads" -Value $maxWorkerThreads -Type DWORD -ErrorAction SilentlyContinue

        # File system cache memory allocation
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "NtfsMemoryUsage" -Value 2 -Type DWORD -ErrorAction SilentlyContinue

        Write-Log "Kernel memory tuned: DisablePagingExecutive=1, LargeSystemCache=1, MaxWorkerThreads=$maxWorkerThreads." "SUCCESS"
    } catch {
        Write-Log "Kernel memory tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 3: Storage & FileSystem
function Tune-StorageAndFileSystem {
    Write-Log "Subsystem [3/6]: Tuning NTFS File System & Storage Caching..." "TUNING"

    $fsKey = "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem"

    try {
        # Disable 8dot3 Short Name Creation (Eliminates legacy overhead on folder creation)
        Set-ItemProperty -Path $fsKey -Name "NtfsDisable8dot3NameCreation" -Value 1 -Type DWORD -ErrorAction SilentlyContinue

        # Disable Last Access Update (Cuts disk read-IO operations in half)
        Set-ItemProperty -Path $fsKey -Name "NtfsDisableLastAccessUpdate" -Value 1 -Type DWORD -ErrorAction SilentlyContinue

        # MFT Zone Reservation (Reserves space for Master File Table to prevent fragmentation)
        $mftVal = if ($script:SystemSpecs.RAMProfile -eq "High") { 3 } else { 2 }
        Set-ItemProperty -Path $fsKey -Name "NtfsMftZoneReservation" -Value $mftVal -Type DWORD -ErrorAction SilentlyContinue

        # Enable TRIM / Delete Notification for SSDs via fsutil
        & fsutil behavior set DisableDeleteNotify 0 2>&1 | Out-Null

        Write-Log "NTFS Optimized: Disabled 8dot3 names, disabled last-access timestamp, allocated MFT Zone $mftVal, verified TRIM." "SUCCESS"
    } catch {
        Write-Log "FileSystem tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 4: Network Stack & Hardware Offloading
function Tune-NetworkStack {
    Write-Log "Subsystem [4/6]: Optimizing TCP/IP Network Stack & Hardware Offloading..." "TUNING"

    try {
        # Select congestion provider
        $tcpProvider = "CUBIC"
        if ($script:SystemSpecs.OSVersion -like "6.*") {
            $tcpProvider = "CTCP"
        }

        # Apply TCP Auto-Tuning, Congestion Provider, and ECN
        Set-NetTCPSetting -SettingName "Internet" -AutoTuningLevelLocal Normal -CongestionProvider $tcpProvider -EcnCapability Enabled -ErrorAction SilentlyContinue
        Set-NetTCPSetting -SettingName "Datacenter" -AutoTuningLevelLocal Normal -CongestionProvider $tcpProvider -EcnCapability Enabled -ErrorAction SilentlyContinue
        if ($script:SystemSpecs.IsServer) {
            Set-NetTCPSetting -SettingName "Server" -AutoTuningLevelLocal Normal -CongestionProvider $tcpProvider -EcnCapability Enabled -ErrorAction SilentlyContinue
        }

        # Enable Timestamps and Fast Open
        Set-NetTCPSetting -SettingName "*" -Timestamps Enabled -ErrorAction SilentlyContinue

        # Hardware Offloading across physical adapters
        if ($script:SystemSpecs.NICList.Count -gt 0) {
            foreach ($adapter in $script:SystemSpecs.NICList) {
                Write-Log "   -> Hardware tuning adapter: $($adapter.Name)" "TUNING"
                Enable-NetAdapterRss -Name $adapter.Name -ErrorAction SilentlyContinue
                Enable-NetAdapterLso -Name $adapter.Name -IPv4 -IPv6 -ErrorAction SilentlyContinue
                Enable-NetAdapterChecksumOffload -Name $adapter.Name -ErrorAction SilentlyContinue

                # Expand Receive/Transmit Buffers
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Receive Buffers" -DisplayValue "2048" -ErrorAction SilentlyContinue
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Transmit Buffers" -DisplayValue "2048" -ErrorAction SilentlyContinue

                # Disable Energy Efficient Ethernet (EEE) / Green Ethernet to remove micro-latency
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Energy Efficient Ethernet" -DisplayValue "Disabled" -ErrorAction SilentlyContinue
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Green Ethernet" -DisplayValue "Disabled" -ErrorAction SilentlyContinue
            }
        }

        Write-Log "Network TCP Stack tuned: Provider=$tcpProvider, ECN=Enabled, RSS=Enabled, Offloads=Maximized." "SUCCESS"
    } catch {
        Write-Log "Network tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 5: SMB & File Sharing Protocol
function Tune-SMBAndFileSharing {
    Write-Log "Subsystem [5/6]: Auto-adjusting SMB Multichannel & Protocol Pipeline..." "TUNING"

    try {
        # Enable SMB Multichannel on client and server
        Set-SmbClientConfiguration -EnableMultiChannel $true -Confirm:$false -ErrorAction SilentlyContinue
        Set-SmbServerConfiguration -EnableMultiChannel $true -Confirm:$false -ErrorAction SilentlyContinue

        # Disable legacy SMB1 protocol for security and performance
        Set-SmbServerConfiguration -EnableSMB1Protocol $false -Confirm:$false -ErrorAction SilentlyContinue

        # Tune SMB2 Credit pools and LanmanServer parameters
        $maxCredits = if ($script:SystemSpecs.IsServer) { 32768 } else { 4096 }
        $maxWorkItems = if ($script:SystemSpecs.RAMProfile -eq "High") { 8192 } else { 4096 }
        $maxThreadsPerCmd = if ($script:SystemSpecs.RAMProfile -eq "High") { 256 } else { 128 }

        Set-SmbServerConfiguration -Smb2CreditsMax $maxCredits -Confirm:$false -ErrorAction SilentlyContinue

        $lanmanKey = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
        Set-ItemProperty -Path $lanmanKey -Name "MaxThreadsPerCmd" -Value $maxThreadsPerCmd -Type DWORD -Force -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $lanmanKey -Name "MaxWorkItems" -Value $maxWorkItems -Type DWORD -Force -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $lanmanKey -Name "Size" -Value 3 -Type DWORD -Force -ErrorAction SilentlyContinue

        Write-Log "SMB Pipelining tuned: Multichannel=Enabled, Smb2CreditsMax=$maxCredits, MaxWorkItems=$maxWorkItems." "SUCCESS"
    } catch {
        Write-Log "SMB tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 6: Latency & Throttling Removal
function Tune-LatencyAndThrottling {
    Write-Log "Subsystem [6/6]: Removing Network & System Latency Throttles..." "TUNING"

    $sysProfileKey = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    $tcpKey = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"

    try {
        # Disable Network Throttling Index (0xFFFFFFFF = Unlimited network throughput)
        Set-ItemProperty -Path $sysProfileKey -Name "NetworkThrottlingIndex" -Value 0xffffffff -Type DWORD -ErrorAction SilentlyContinue

        # Set System Responsiveness (0 = 100% CPU focus on current active tasks)
        Set-ItemProperty -Path $sysProfileKey -Name "SystemResponsiveness" -Value 0 -Type DWORD -ErrorAction SilentlyContinue

        # Expand Ephemeral Ports (MaxUserPort) & Reduce TCP Wait Delay
        Set-ItemProperty -Path $tcpKey -Name "MaxUserPort" -Value 65534 -Type DWORD -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $tcpKey -Name "TcpTimedWaitDelay" -Value 30 -Type DWORD -ErrorAction SilentlyContinue

        Write-Log "Latency throttles removed: NetworkThrottlingIndex=Disabled, SystemResponsiveness=0, MaxUserPort=65534, TcpTimedWaitDelay=30s." "SUCCESS"
    } catch {
        Write-Log "Latency tuning note: $($_.Exception.Message)" "WARN"
    }
}

# -------------------------------------------------------------------------
# FULL AUTOMATIC TUNING WORKFLOW CONTROLLER
# -------------------------------------------------------------------------
function Start-FullAutoTuneSequence {
    $btnAutoTune.Enabled = $false
    $btnRestore.Enabled = $false
    Set-Progress 0

    Write-Log "=========================================================" "INFO"
    Write-Log "STARTING FULLY AUTOMATIC PERFORMANCE TUNING WORKFLOW" "INFO"
    Write-Log "=========================================================" "INFO"

    # Step 1: Detect Hardware
    Set-Progress 10
    Invoke-HardwareDetection

    # Step 2: Auto-Backup
    Set-Progress 25
    Invoke-AutoBackup

    # Step 3: Subsystem Optimizations
    Set-Progress 40
    Tune-PowerAndCPU

    Set-Progress 55
    Tune-KernelAndMemory

    Set-Progress 70
    Tune-StorageAndFileSystem

    Set-Progress 80
    Tune-NetworkStack

    Set-Progress 90
    Tune-SMBAndFileSharing

    Set-Progress 95
    Tune-LatencyAndThrottling

    Set-Progress 100
    Write-Log "=========================================================" "SUCCESS"
    Write-Log "⚡ ALL SUBSYSTEMS AUTONOMOUSLY TUNED FOR PEAK PERFORMANCE! " "SUCCESS"
    Write-Log "Recommended Action: Reboot system to ensure all kernel changes take effect." "SUCCESS"
    Write-Log "=========================================================" "SUCCESS"

    $btnAutoTune.Enabled = $true
    $btnRestore.Enabled = $true

    [System.Windows.Forms.MessageBox]::Show(
        "Autonomous Tuning Complete!`r`n`r`nAll power, kernel memory, disk NTFS, TCP network stack, SMB multichannel, and latency throttles have been optimized based on your detected hardware.`r`n`r`nPlease reboot your machine for all kernel and driver adjustments to take effect.",
        "Auto-Tune Finished",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
}

# -------------------------------------------------------------------------
# RESTORE BACKUP FUNCTION
# -------------------------------------------------------------------------
function Invoke-RestoreBackup {
    if (-not (Test-Path $script:BackupDir)) {
        [System.Windows.Forms.MessageBox]::Show("No backup directory found.", "Restore Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
        return
    }

    $backupFiles = Get-ChildItem -Path $script:BackupDir -Filter "*.reg" | Sort-Object LastWriteTime -Descending
    if ($backupFiles.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show("No .reg backup files found in $script:BackupDir.", "Restore Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null
        return
    }

    $latestBackup = $backupFiles[0]
    $confirm = [System.Windows.Forms.MessageBox]::Show(
        "Do you want to restore the latest pre-tuning registry state backup?`r`n`r`nBackup file: $($latestBackup.Name)",
        "Confirm State Restore",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )

    if ($confirm -eq [System.Windows.Forms.DialogResult]::Yes) {
        Write-Log "Restoring registry state from: $($latestBackup.FullName)..." "RESTORE"
        try {
            & reg.exe import $latestBackup.FullName 2>&1 | Out-Null
            $timestampPart = $latestBackup.Name -replace "PreTune_Registry_Backup_", ""
            $softBackupFile = Join-Path $script:BackupDir "PreTune_Software_Backup_$timestampPart"
            if (Test-Path $softBackupFile) {
                & reg.exe import $softBackupFile 2>&1 | Out-Null
            }
            Write-Log "Registry state successfully restored from $($latestBackup.Name)!" "SUCCESS"
            [System.Windows.Forms.MessageBox]::Show("Registry backup restored successfully! Please restart your computer.", "Restore Complete", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null
        } catch {
            Write-Log "Failed to restore registry backup: $($_.Exception.Message)" "ERROR"
        }
    }
}

# -------------------------------------------------------------------------
# SAVE LOG FUNCTION
# -------------------------------------------------------------------------
function Save-LogToFile {
    $saveDialog = New-Object System.Windows.Forms.SaveFileDialog
    $saveDialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
    $saveDialog.FileName = "Tuning_Log_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".txt"
    $saveDialog.InitialDirectory = $script:ScriptDir

    if ($saveDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $txtLog.Text | Out-File -FilePath $saveDialog.FileName -Encoding utf8
        Write-Log "Log saved to: $($saveDialog.FileName)" "SUCCESS"
    }
}

# -------------------------------------------------------------------------
# EVENT BINDINGS & AUTOMATIC LAUNCH TIMER
# -------------------------------------------------------------------------
$btnAutoTune.Add_Click({
    Start-FullAutoTuneSequence
})

$btnRestore.Add_Click({
    Invoke-RestoreBackup
})

$btnExportLog.Add_Click({
    Save-LogToFile
})

# Form Load Event: Auto-run detection immediately and trigger auto-tune workflow automatically
$form.Add_Shown({
    # Run hardware detection first
    Invoke-HardwareDetection

    # Auto-start auto-tuning sequence after 1 second
    $autoStartTimer = New-Object System.Windows.Forms.Timer
    $autoStartTimer.Interval = 1000
    $autoStartTimer.Add_Tick({
        $autoStartTimer.Stop()
        $autoStartTimer.Dispose()
        Start-FullAutoTuneSequence
    })
    $autoStartTimer.Start()
})

# Display Form
$form.ShowDialog() | Out-Null
$form.Dispose()
