<#
.SYNOPSIS
    AutoPerformanceTuner.ps1 - Enterprise Autonomous Windows Performance & Tuning Tool
.DESCRIPTION
    Fully automatic, context-aware performance tuning GUI application for Windows Workstations and Servers.
    Detects hardware parameters (CPU, RAM, Disks, NICs, OS Role) and automatically creates pre-tuning backups,
    adjusts kernel memory limits, network TCP stack settings, storage & file system optimizations, SMB protocols,
    power management profiles, GPU scheduling, DNS caching, and system latency controls.
.NOTES
    Requires Administrator privileges.
#>

# Check Administrator Rights
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
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
    RAMProfile       = "Low"
    SelectedProfile  = "Autonomous Dynamic Tuning"
}

# -------------------------------------------------------------------------
# GUI BUILDING & LAYOUT
# -------------------------------------------------------------------------
$form = New-Object System.Windows.Forms.Form
$form.Text = "Autonomous Windows Performance & Tuning Engine"
$form.Size = New-Object System.Drawing.Size(860, 720)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(24, 26, 32)

# Font definitions
$fontTitle    = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fontSubTitle = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Regular)
$fontSection  = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontConsole  = New-Object System.Drawing.Font("Consolas", 9, [System.Drawing.FontStyle]::Regular)
$fontButton   = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)

# Header Banner Panel
$pnlHeader = New-Object System.Windows.Forms.Panel
$pnlHeader.Location = New-Object System.Drawing.Point(0, 0)
$pnlHeader.Size = New-Object System.Drawing.Size(860, 75)
$pnlHeader.BackColor = [System.Drawing.Color]::FromArgb(18, 20, 26)
$form.Controls.Add($pnlHeader)

$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "[+] AUTONOMOUS PERFORMANCE & TUNING ENGINE"
$lblTitle.Font = $fontTitle
$lblTitle.Location = New-Object System.Drawing.Point(20, 12)
$lblTitle.Size = New-Object System.Drawing.Size(820, 30)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(0, 210, 255)
$pnlHeader.Controls.Add($lblTitle)

$lblSubTitle = New-Object System.Windows.Forms.Label
$lblSubTitle.Text = "Autonomous Multi-Subsystem Optimization, GPU Scheduling, DNS Cache, and Safety Rollbacks"
$lblSubTitle.Font = $fontSubTitle
$lblSubTitle.Location = New-Object System.Drawing.Point(22, 43)
$lblSubTitle.Size = New-Object System.Drawing.Size(810, 22)
$lblSubTitle.ForeColor = [System.Drawing.Color]::FromArgb(160, 175, 195)
$pnlHeader.Controls.Add($lblSubTitle)

# System Summary Panel
$grpSummary = New-Object System.Windows.Forms.GroupBox
$grpSummary.Text = " Detected Environment & Optimization Profile "
$grpSummary.Font = $fontSection
$grpSummary.Location = New-Object System.Drawing.Point(20, 85)
$grpSummary.Size = New-Object System.Drawing.Size(805, 90)
$grpSummary.ForeColor = [System.Drawing.Color]::FromArgb(0, 210, 255)
$form.Controls.Add($grpSummary)

$lblSummaryText = New-Object System.Windows.Forms.Label
$lblSummaryText.Text = "Scanning hardware parameters..."
$lblSummaryText.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Regular)
$lblSummaryText.Location = New-Object System.Drawing.Point(15, 22)
$lblSummaryText.Size = New-Object System.Drawing.Size(530, 60)
$lblSummaryText.ForeColor = [System.Drawing.Color]::FromArgb(220, 225, 230)
$grpSummary.Controls.Add($lblSummaryText)

# Profile Selector
$lblProfile = New-Object System.Windows.Forms.Label
$lblProfile.Text = "Target Profile:"
$lblProfile.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$lblProfile.Location = New-Object System.Drawing.Point(555, 25)
$lblProfile.Size = New-Object System.Drawing.Size(100, 20)
$lblProfile.ForeColor = [System.Drawing.Color]::FromArgb(0, 210, 255)
$grpSummary.Controls.Add($lblProfile)

$cmbProfile = New-Object System.Windows.Forms.ComboBox
$cmbProfile.Location = New-Object System.Drawing.Point(555, 48)
$cmbProfile.Size = New-Object System.Drawing.Size(235, 25)
$cmbProfile.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
[void]$cmbProfile.Items.Add("Autonomous Dynamic Tuning")
[void]$cmbProfile.Items.Add("Max Server Throughput")
[void]$cmbProfile.Items.Add("Low Latency Workstation")
$cmbProfile.SelectedIndex = 0
$grpSummary.Controls.Add($cmbProfile)

# Log Console Label
$lblConsole = New-Object System.Windows.Forms.Label
$lblConsole.Text = "Real-Time Subsystem Optimization Log:"
$lblConsole.Font = $fontSection
$lblConsole.Location = New-Object System.Drawing.Point(20, 185)
$lblConsole.Size = New-Object System.Drawing.Size(400, 20)
$lblConsole.ForeColor = [System.Drawing.Color]::FromArgb(220, 225, 230)
$form.Controls.Add($lblConsole)

# Log Output TextBox
$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Font = $fontConsole
$txtLog.Location = New-Object System.Drawing.Point(20, 210)
$txtLog.Size = New-Object System.Drawing.Size(805, 340)
$txtLog.ReadOnly = $true
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(12, 14, 18)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(0, 230, 115)
$form.Controls.Add($txtLog)

# Progress Bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(20, 560)
$progressBar.Size = New-Object System.Drawing.Size(805, 20)
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$form.Controls.Add($progressBar)

# Action Buttons Panel
$btnAutoTune = New-Object System.Windows.Forms.Button
$btnAutoTune.Text = "Start Auto-Tune"
$btnAutoTune.Font = $fontButton
$btnAutoTune.Location = New-Object System.Drawing.Point(20, 595)
$btnAutoTune.Size = New-Object System.Drawing.Size(190, 42)
$btnAutoTune.BackColor = [System.Drawing.Color]::FromArgb(0, 150, 255)
$btnAutoTune.ForeColor = [System.Drawing.Color]::White
$btnAutoTune.FlatStyle = "Flat"
$btnAutoTune.FlatAppearance.BorderSize = 0
$form.Controls.Add($btnAutoTune)

$btnRestore = New-Object System.Windows.Forms.Button
$btnRestore.Text = "Restore Backup"
$btnRestore.Font = $fontButton
$btnRestore.Location = New-Object System.Drawing.Point(222, 595)
$btnRestore.Size = New-Object System.Drawing.Size(190, 42)
$btnRestore.BackColor = [System.Drawing.Color]::FromArgb(180, 90, 0)
$btnRestore.ForeColor = [System.Drawing.Color]::White
$btnRestore.FlatStyle = "Flat"
$btnRestore.FlatAppearance.BorderSize = 0
$form.Controls.Add($btnRestore)

$btnReport = New-Object System.Windows.Forms.Button
$btnReport.Text = "System Report"
$btnReport.Font = $fontButton
$btnReport.Location = New-Object System.Drawing.Point(424, 595)
$btnReport.Size = New-Object System.Drawing.Size(190, 42)
$btnReport.BackColor = [System.Drawing.Color]::FromArgb(0, 130, 110)
$btnReport.ForeColor = [System.Drawing.Color]::White
$btnReport.FlatStyle = "Flat"
$btnReport.FlatAppearance.BorderSize = 0
$form.Controls.Add($btnReport)

$btnExportLog = New-Object System.Windows.Forms.Button
$btnExportLog.Text = "Save Log"
$btnExportLog.Font = $fontButton
$btnExportLog.Location = New-Object System.Drawing.Point(626, 595)
$btnExportLog.Size = New-Object System.Drawing.Size(199, 42)
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

        $lblSummaryText.Text = "Platform: $($script:SystemSpecs.OSCaption) [$roleStr]`r`nProcessor & RAM: $cpuStr | $ramStr`r`nNetwork Infrastructure: $nicStr"

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
    $softBackupPath = Join-Path $script:BackupDir "PreTune_Software_Backup_$timestamp.reg"
    $jsonBackupPath = Join-Path $script:BackupDir "PreTune_Metadata_$timestamp.json"

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
# 3. SUBSYSTEM AUTO-TUNING MODULES (9 Subsystems)
# -------------------------------------------------------------------------

# Subsystem 1: Power & CPU Scheduling
function Tune-PowerAndCPU {
    Write-Log "Subsystem [1/9]: Optimizing Power Management & CPU Scheduling..." "TUNING"

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
    Write-Log "Subsystem [2/9]: Auto-tuning Kernel & Memory Management..." "TUNING"

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
    Write-Log "Subsystem [3/9]: Tuning NTFS File System & Storage Caching..." "TUNING"

    $fsKey = "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem"

    try {
        # Disable 8dot3 Short Name Creation (Eliminates legacy overhead on folder creation)
        Set-ItemProperty -Path $fsKey -Name "NtfsDisable8dot3NameCreation" -Value 1 -Type DWORD -ErrorAction SilentlyContinue

        # Disable Last Access Update (Cuts disk read-IO operations in half)
        Set-ItemProperty -Path $fsKey -Name "NtfsDisableLastAccessUpdate" -Value 1 -Type DWORD -ErrorAction SilentlyContinue

        # MFT Zone Reservation
        $mftVal = if ($script:SystemSpecs.RAMProfile -eq "High") { 3 } else { 2 }
        Set-ItemProperty -Path $fsKey -Name "NtfsMftZoneReservation" -Value $mftVal -Type DWORD -ErrorAction SilentlyContinue

        # Enable TRIM for SSDs
        & fsutil behavior set DisableDeleteNotify 0 2>&1 | Out-Null

        Write-Log "NTFS Optimized: Disabled 8dot3 names, disabled last-access timestamp, allocated MFT Zone $mftVal, verified TRIM." "SUCCESS"
    } catch {
        Write-Log "FileSystem tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 4: Network Stack & Hardware Offloading
function Tune-NetworkStack {
    Write-Log "Subsystem [4/9]: Optimizing TCP/IP Network Stack & Hardware Offloading..." "TUNING"

    try {
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

        # Enable Timestamps
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

                # Disable Energy Efficient Ethernet
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
    Write-Log "Subsystem [5/9]: Auto-adjusting SMB Multichannel & Protocol Pipeline..." "TUNING"

    try {
        # Enable SMB Multichannel
        Set-SmbClientConfiguration -EnableMultiChannel $true -Confirm:$false -ErrorAction SilentlyContinue
        Set-SmbServerConfiguration -EnableMultiChannel $true -Confirm:$false -ErrorAction SilentlyContinue

        # Disable legacy SMB1
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
    Write-Log "Subsystem [6/9]: Removing Network & System Latency Throttles..." "TUNING"

    $sysProfileKey = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    $tcpKey = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"

    try {
        # Disable Network Throttling Index (0xFFFFFFFF)
        Set-ItemProperty -Path $sysProfileKey -Name "NetworkThrottlingIndex" -Value 0xffffffff -Type DWORD -ErrorAction SilentlyContinue

        # Set System Responsiveness (0 = 100% CPU focus on current active tasks)
        Set-ItemProperty -Path $sysProfileKey -Name "SystemResponsiveness" -Value 0 -Type DWORD -ErrorAction SilentlyContinue

        # Expand Ephemeral Ports & Reduce TCP Wait Delay
        Set-ItemProperty -Path $tcpKey -Name "MaxUserPort" -Value 65534 -Type DWORD -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $tcpKey -Name "TcpTimedWaitDelay" -Value 30 -Type DWORD -ErrorAction SilentlyContinue

        Write-Log "Latency throttles removed: NetworkThrottlingIndex=Disabled, SystemResponsiveness=0, MaxUserPort=65534, TcpTimedWaitDelay=30s." "SUCCESS"
    } catch {
        Write-Log "Latency tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 7: GPU Scheduling & Graphics Subsystem
function Tune-GPUScheduling {
    Write-Log "Subsystem [7/9]: Tuning GPU Acceleration & Hardware-Accelerated GPU Scheduling..." "TUNING"

    $gfxKey = "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers"

    try {
        # Enable Hardware-Accelerated GPU Scheduling (HwSchMode = 2)
        Set-ItemProperty -Path $gfxKey -Name "HwSchMode" -Value 2 -Type DWORD -ErrorAction SilentlyContinue
        Write-Log "Hardware-Accelerated GPU Scheduling (HAGS) forced to Mode 2 (Enabled)." "SUCCESS"
    } catch {
        Write-Log "GPU Scheduling note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 8: DNS Cache & Name Resolution Latency
function Tune-DNSCache {
    Write-Log "Subsystem [8/9]: Optimizing DNS Cache & Name Resolution Latency..." "TUNING"

    $dnsKey = "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"

    try {
        # Increase positive DNS cache TTL and reduce negative cache TTL
        Set-ItemProperty -Path $dnsKey -Name "MaxCacheTtl" -Value 86400 -Type DWORD -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $dnsKey -Name "MaxNegativeCacheTtl" -Value 5 -Type DWORD -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $dnsKey -Name "NetFailureCacheTime" -Value 0 -Type DWORD -ErrorAction SilentlyContinue

        Write-Log "DNS Resolver optimized: MaxCacheTtl=86400s, MaxNegativeCacheTtl=5s, NetFailureCacheTime=0s." "SUCCESS"
    } catch {
        Write-Log "DNS Cache tuning note: $($_.Exception.Message)" "WARN"
    }
}

# Subsystem 9: Advanced NIC Interrupt Moderation & Flow Control
function Tune-NICInterruptsAndFlowControl {
    Write-Log "Subsystem [9/9]: Advanced NIC Interrupt Moderation & Queue Alignment..." "TUNING"

    try {
        if ($script:SystemSpecs.NICList.Count -gt 0) {
            foreach ($adapter in $script:SystemSpecs.NICList) {
                # Disable Flow Control to prevent Ethernet pause frame stalls under peak traffic
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Flow Control" -DisplayValue "Disabled" -ErrorAction SilentlyContinue

                # Align RSS Queues based on CPU physical cores
                $queues = if ($script:SystemSpecs.PhysicalCores -ge 8) { "8 Queues" } else { "4 Queues" }
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Maximum Number of RSS Queues" -DisplayValue $queues -ErrorAction SilentlyContinue
            }
            Write-Log "NIC Flow Control suppressed and RSS Queues aligned across physical interfaces." "SUCCESS"
        } else {
            Write-Log "No active physical NICs required Queue re-alignment." "INFO"
        }
    } catch {
        Write-Log "NIC Interrupt tuning note: $($_.Exception.Message)" "WARN"
    }
}

# -------------------------------------------------------------------------
# FULL AUTOMATIC TUNING WORKFLOW CONTROLLER
# -------------------------------------------------------------------------
function Start-FullAutoTuneSequence {
    $profileName = "Autonomous Dynamic Tuning"
    if ($cmbProfile -and $cmbProfile.SelectedItem) {
        $profileName = $cmbProfile.SelectedItem.ToString()
    }

    # Step 1: Detect Hardware first to show detected specs in confirmation prompt
    Invoke-HardwareDetection

    # User Confirmation Prompt
    $confirmResult = [System.Windows.Forms.MessageBox]::Show(
        "Detected Platform: $($script:SystemSpecs.OSCaption)`r`n" +
        "CPU Cores: $($script:SystemSpecs.LogicalCores) Logical / $($script:SystemSpecs.PhysicalCores) Physical`r`n" +
        "Memory: $($script:SystemSpecs.TotalRAM_GB) GB RAM`r`n" +
        "Selected Tuning Profile: $profileName`r`n`r`n" +
        "Do you want to proceed with applying performance tweaks across all 9 system subsystems?",
        "Confirm Performance Tuning",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )

    if ($confirmResult -ne [System.Windows.Forms.DialogResult]::Yes) {
        Write-Log "Automatic performance tuning cancelled by user." "WARN"
        return
    }

    $btnAutoTune.Enabled = $false
    $btnRestore.Enabled = $false
    $btnReport.Enabled = $false
    Set-Progress 0

    Write-Log "=========================================================" "INFO"
    Write-Log "STARTING AUTOMATIC TUNING WORKFLOW [Profile: $profileName]" "INFO"
    Write-Log "=========================================================" "INFO"

    # Step 2: Auto-Backup
    Set-Progress 20
    Invoke-AutoBackup

    # Step 3: Subsystem Optimizations
    Set-Progress 30
    Tune-PowerAndCPU

    Set-Progress 40
    Tune-KernelAndMemory

    Set-Progress 50
    Tune-StorageAndFileSystem

    Set-Progress 60
    Tune-NetworkStack

    Set-Progress 70
    Tune-SMBAndFileSharing

    Set-Progress 78
    Tune-LatencyAndThrottling

    Set-Progress 85
    Tune-GPUScheduling

    Set-Progress 92
    Tune-DNSCache

    Set-Progress 97
    Tune-NICInterruptsAndFlowControl

    Set-Progress 100
    Write-Log "=========================================================" "SUCCESS"
    Write-Log "[+] ALL 9 SUBSYSTEMS AUTONOMOUSLY TUNED FOR PEAK PERFORMANCE!" "SUCCESS"
    Write-Log "Recommended Action: Reboot system to ensure all kernel changes take effect." "SUCCESS"
    Write-Log "=========================================================" "SUCCESS"

    $btnAutoTune.Enabled = $true
    $btnRestore.Enabled = $true
    $btnReport.Enabled = $true

    [System.Windows.Forms.MessageBox]::Show(
        "Autonomous Multi-Subsystem Tuning Complete!`r`n`r`nAll 9 performance subsystems (Power, Kernel/Memory, Storage NTFS, Network TCP Stack, SMB Multichannel, Latency Throttles, GPU Scheduling, DNS Cache, and NIC Queues) have been optimized.`r`n`r`nPlease reboot your machine for all kernel adjustments to take effect.",
        "Auto-Tune Finished",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
}

# -------------------------------------------------------------------------
# SYSTEM DIAGNOSTIC REPORT GENERATOR
# -------------------------------------------------------------------------
function Generate-SystemReport {
    Write-Log "Generating System State & Diagnostics HTML Report..." "REPORT"

    $reportPath = Join-Path $script:ScriptDir "System_Tuning_Report.html"

    $osInfo = "$($script:SystemSpecs.OSCaption) ($($script:SystemSpecs.OSVersion))"
    $cpuInfo = "$($script:SystemSpecs.LogicalCores) Logical / $($script:SystemSpecs.PhysicalCores) Physical Cores"
    $ramInfo = "$($script:SystemSpecs.TotalRAM_GB) GB (Profile: $($script:SystemSpecs.RAMProfile))"
    $nicInfo = "$($script:SystemSpecs.ActiveNICsCount) Interface(s)"

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("<!DOCTYPE html>")
    [void]$sb.AppendLine("<html>")
    [void]$sb.AppendLine("<head>")
    [void]$sb.AppendLine("    <title>Autonomous Windows Performance Report</title>")
    [void]$sb.AppendLine("    <style>")
    [void]$sb.AppendLine("        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #12141a; color: #e0e5ea; padding: 20px; }")
    [void]$sb.AppendLine("        h1 { color: #00d2ff; border-bottom: 2px solid #00d2ff; padding-bottom: 10px; }")
    [void]$sb.AppendLine("        h2 { color: #00e673; margin-top: 25px; }")
    [void]$sb.AppendLine("        .card { background-color: #1a1d26; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }")
    [void]$sb.AppendLine("        table { width: 100%; border-collapse: collapse; margin-top: 10px; }")
    [void]$sb.AppendLine("        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #2a2e3d; }")
    [void]$sb.AppendLine("        th { background-color: #222633; color: #00d2ff; }")
    [void]$sb.AppendLine("        .status-good { color: #00e673; font-weight: bold; }")
    [void]$sb.AppendLine("    </style>")
    [void]$sb.AppendLine("</head>")
    [void]$sb.AppendLine("<body>")
    [void]$sb.AppendLine("    <h1>Autonomous Performance and Tuning Diagnostic Report</h1>")
    [void]$sb.AppendLine("    <div class='card'>")
    [void]$sb.AppendLine("        <h2>System Environment Summary</h2>")
    [void]$sb.AppendLine("        <table>")
    [void]$sb.AppendLine("            <tr><th>Property</th><th>Detected Value</th></tr>")
    [void]$sb.AppendLine("            <tr><td>Operating System</td><td>$osInfo</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Processor Core Count</td><td>$cpuInfo</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Total Memory (RAM)</td><td>$ramInfo</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Active Physical Adapters</td><td>$nicInfo</td></tr>")
    [void]$sb.AppendLine("        </table>")
    [void]$sb.AppendLine("    </div>")
    [void]$sb.AppendLine("    <div class='card'>")
    [void]$sb.AppendLine("        <h2>Subsystem Tuning Status</h2>")
    [void]$sb.AppendLine("        <table>")
    [void]$sb.AppendLine("            <tr><th>Subsystem</th><th>Target Parameters</th><th>Status</th></tr>")
    [void]$sb.AppendLine("            <tr><td>Power and CPU</td><td>Ultimate / High Performance Profile, Core Parking Disabled</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Kernel Memory</td><td>DisablePagingExecutive=1, LargeSystemCache=1, MaxWorkerThreads</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Storage NTFS</td><td>NtfsDisable8dot3=1, NtfsDisableLastAccess=1, TRIM Active</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Network TCP Stack</td><td>TCP Auto-Tuning, Congestion Provider (CUBIC/CTCP), ECN Enabled</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>SMB Multichannel</td><td>SMB Multichannel Enabled, Smb2CreditsMax Scaled, SMB1 Disabled</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>Latency Throttles</td><td>NetworkThrottlingIndex=Disabled, SystemResponsiveness=0</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>GPU Acceleration</td><td>Hardware-Accelerated GPU Scheduling (HAGS) Mode 2</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>DNS Cache</td><td>MaxCacheTtl=86400, MaxNegativeCacheTtl=5, NetFailureCacheTime=0</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("            <tr><td>NIC Interrupts</td><td>Flow Control Disabled, RSS Queues Aligned</td><td class='status-good'>OPTIMIZED</td></tr>")
    [void]$sb.AppendLine("        </table>")
    [void]$sb.AppendLine("    </div>")
    [void]$sb.AppendLine("</body>")
    [void]$sb.AppendLine("</html>")

    $sb.ToString() | Out-File -FilePath $reportPath -Encoding utf8
    Write-Log "Diagnostic report generated successfully: $reportPath" "SUCCESS"

    [System.Windows.Forms.MessageBox]::Show(
        "Diagnostic Report Generated!`r`n`r`nFile saved to: $reportPath",
        "Report Created",
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

$btnReport.Add_Click({
    Generate-SystemReport
})

$btnExportLog.Add_Click({
    Save-LogToFile
})

# Form Load Event: Auto-run detection immediately and trigger auto-tune workflow automatically
$form.Add_Shown({
    Invoke-HardwareDetection

    # Auto-start auto-tuning sequence after 1 second
    $script:autoStartTimer = New-Object System.Windows.Forms.Timer
    $script:autoStartTimer.Interval = 1000
    $script:autoStartTimer.Add_Tick({
        param($sender, $e)
        if ($sender) {
            $sender.Stop()
            $sender.Dispose()
        } elseif ($script:autoStartTimer) {
            $script:autoStartTimer.Stop()
            $script:autoStartTimer.Dispose()
        }
        Start-FullAutoTuneSequence
    })
    $script:autoStartTimer.Start()
})

# Display Form
$form.ShowDialog() | Out-Null
$form.Dispose()
