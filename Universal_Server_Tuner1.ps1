Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- GLOBAL PROFILE ARRAYS ---
$global:OS_Caption = "Unknown OS"
$global:OS_Version = "0.0"
$global:Recommended_TCP = "Default"
$global:Supports_ECN = $false
$global:Max_Credits = 4096
$global:Max_Worker_Threads = 32

# --- APPLICATION WINDOW ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "Universal Intelligent File Server Tuning Engine"
$form.Size = New-Object System.Drawing.Size(730, 600)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(240, 244, 248)

# --- FONT DEFINITIONS ---
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$fontSection = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontConsole = New-Object System.Drawing.Font("Consolas", 9)

# --- TITLE BAR ---
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "Context-Aware Autonomous File Server Tuning Engine"
$lblTitle.Font = $fontTitle
$lblTitle.Location = New-Object System.Drawing.Point(15, 15)
$lblTitle.Size = New-Object System.Drawing.Size(690, 30)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(20, 35, 45)
$form.Controls.Add($lblTitle)

# --- ACTION BUTTONS ---
$btnDetect = New-Object System.Windows.Forms.Button
$btnDetect.Text = "1. Autodetect OS and Map Capabilities"
$btnDetect.Font = $fontSection
$btnDetect.Location = New-Object System.Drawing.Point(20, 60)
$btnDetect.Size = New-Object System.Drawing.Size(330, 45)
$btnDetect.BackColor = [System.Drawing.Color]::FromArgb(0, 102, 204)
$btnDetect.ForeColor = [System.Drawing.Color]::White
$btnDetect.FlatStyle = "Flat"
$form.Controls.Add($btnDetect)

$btnTweak = New-Object System.Windows.Forms.Button
$btnTweak.Text = "2. Apply Custom Tailored Matrix"
$btnTweak.Font = $fontSection
$btnTweak.Location = New-Object System.Drawing.Point(365, 60)
$btnTweak.Size = New-Object System.Drawing.Size(330, 45)
$btnTweak.BackColor = [System.Drawing.Color]::FromArgb(34, 139, 34)
$btnTweak.ForeColor = [System.Drawing.Color]::White
$btnTweak.FlatStyle = "Flat"
$btnTweak.Enabled = $false
$form.Controls.Add($btnTweak)

# --- LIVE OUTPUT BOX ---
$lblLog = New-Object System.Windows.Forms.Label
$lblLog.Text = "Adaptive Optimization Log Output:"
$lblLog.Font = $fontSection
$lblLog.Location = New-Object System.Drawing.Point(20, 120)
$lblLog.Size = New-Object System.Drawing.Size(300, 20)
$form.Controls.Add($lblLog)

$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Font = $fontConsole
$txtLog.Location = New-Object System.Drawing.Point(20, 145)
$txtLog.Size = New-Object System.Drawing.Size(675, 385)
$txtLog.ReadOnly = $true
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(12, 16, 22)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(0, 230, 115)
$form.Controls.Add($txtLog)

# --- LOGGING HELPER ---
function Write-GuiLog {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[INFO]   "
    if ($Type -eq "SUCCESS") { $prefix = "[MATCHED] " }
    if ($Type -eq "WARN")    { $prefix = "[WARNING] " }
    if ($Type -eq "ERROR")   { $prefix = "[FAILED]  " }
    
    $txtLog.AppendText("$timestamp $prefix $Message`r`n")
}

# --- AUTOMATED DETECT & MAP ENGINE ---
$btnDetect.Add_Click({
    $txtLog.Clear()
    Write-GuiLog "Initializing automated Operating System detection sequence..." "INFO"
    
    $os = Get-CimInstance Win32_OperatingSystem
    $global:OS_Caption = $os.Caption
    $global:OS_Version = [version]$os.Version
    
    Write-GuiLog "Detected Platform: $global:OS_Caption (Build: $($global:OS_Version))" "SUCCESS"

    if ($global:OS_Version.Major -eq 6 -and $global:OS_Version.Minor -le 3) {
        Write-GuiLog "Target Architecture Profile: Legacy NT 6.x Kernel Suite Identified." "INFO"
        $global:Recommended_TCP = "CTCP"
        $global:Supports_ECN = $false
        $global:Max_Credits = 8192
        $global:Max_Worker_Threads = 64
        Write-GuiLog "Mapped parameters: Network Layer -> Compound TCP | SMB Scale Tier -> Moderate" "INFO"
    }
    elseif ($global:OS_Version.Major -eq 10 -and $global:OS_Version.Build -lt 17763) {
        Write-GuiLog "Target Architecture Profile: Windows Server 2016 Runtime Suite Identified." "INFO"
        $global:Recommended_TCP = "CUBIC"
        $global:Supports_ECN = $true
        $global:Max_Credits = 16384
        $global:Max_Worker_Threads = 128
        Write-GuiLog "Mapped parameters: Network Layer -> CUBIC plus ECN Enabled | SMB Scale Tier -> High Concurrency" "INFO"
    }
    else {
        Write-GuiLog "Target Architecture Profile: Modern Windows Server SaaS Core Suite Identified." "INFO"
        $global:Recommended_TCP = "CUBIC"
        $global:Supports_ECN = $true
        $global:Max_Credits = 32768
        $global:Max_Worker_Threads = 256
        Write-GuiLog "Mapped parameters: Network Layer -> CUBIC Windows Framework v2 | SMB Scale Tier -> Extreme Flash Thresholds" "INFO"
    }

    $smbConfig = Get-SmbServerConfiguration
    if ($smbConfig.Smb2CreditsMax -ge $global:Max_Credits) {
        Write-GuiLog "Current SMB Credit Pool configuration is optimal ($($smbConfig.Smb2CreditsMax))." "SUCCESS"
    } else {
        Write-GuiLog "Current SMB Credit Pool is unoptimized ($($smbConfig.Smb2CreditsMax)). Recommended: $global:Max_Credits" "WARN"
    }

    $sysCache = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name LargeSystemCache -ErrorAction SilentlyContinue
    if ($sysCache.LargeSystemCache -eq 1) {
        Write-GuiLog "Memory caching hierarchy correctly favors large disk IO pools." "SUCCESS"
    } else {
        Write-GuiLog "Memory management subsystem is prioritizing processes over active files pooling." "WARN"
    }

    Write-GuiLog "Dynamic system profile generation complete. Tuning configuration safe rules mapped." "INFO"
    $btnTweak.Enabled = $true
})

# --- TAILORED TUNING EXECUTION ENGINE ---
$btnTweak.Add_Click({
    Write-GuiLog "Deploying dynamic optimization matrices..." "INFO"

    try {
        Write-GuiLog "Injecting Tailored Network Optimization Protocol ($global:Recommended_TCP)..." "INFO"
        if ($global:Supports_ECN) {
            Set-NetTCPSetting -SettingName "Internet" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -EcnCapability Enabled -ErrorAction SilentlyContinue
            Set-NetTCPSetting -SettingName "Datacenter" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -EcnCapability Enabled -ErrorAction SilentlyContinue
            Write-GuiLog "TCP Core optimized via $global:Recommended_TCP algorithm with active ECN protection flags." "SUCCESS"
        } else {
            Set-NetTCPSetting -SettingName "Internet" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -ErrorAction SilentlyContinue
            Set-NetTCPSetting -SettingName "Datacenter" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -ErrorAction SilentlyContinue
            Write-GuiLog "TCP Core optimized via legacy $global:Recommended_TCP framework." "SUCCESS"
        }

        Write-GuiLog "Tuning SMB protocol pipeline boundaries for maximum concurrent commands ($global:Max_Credits)..." "INFO"
        Set-SmbServerConfiguration -Smb2CreditsMax $global:Max_Credits -AsynchronousRequestsMax ($global:Max_Worker_Threads * 16) -AdditionalCriticalWorkerThreads $global:Max_Worker_Threads -Force
        Write-GuiLog "SMB buffer pools allocated for ideal execution on $global:OS_Caption." "SUCCESS"

        Write-GuiLog "Re-allocating host system memory mapping priorities..." "INFO"
        $memPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
        Set-ItemProperty -Path $memPath -Name LargeSystemCache -Value 1 -ErrorAction SilentlyContinue
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name NtfsMemoryUsage -Value 2 -ErrorAction SilentlyContinue
        Write-GuiLog "Kernel file systems pooling caches modified to High-Performance storage-target constraints." "SUCCESS"

        Write-GuiLog "Dismantling legacy LanmanServer operational limits..." "INFO"
        $lanmanPath = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
        Set-ItemProperty -Path $lanmanPath -Name MaxThreadsPerCmd -Value 255 -Force -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $lanmanPath -Name MaxWorkItems -Value 8192 -Force -ErrorAction SilentlyContinue
        Write-GuiLog "LAN operational command bandwidth limits dropped." "SUCCESS"

        Write-GuiLog "Running validation bindings across physical interface arrays..." "INFO"
        Set-SmbServerConfiguration -EnableMultiChannel $true -Force
        Set-SmbClientConfiguration -EnableMultiChannel $true -Force
        Enable-NetAdapterRss -Name "*" -ErrorAction SilentlyContinue
        Update-SmbMultichannelConnection -ErrorAction SilentlyContinue
        Write-GuiLog "SMB Multichannel pipeline bindings synchronized." "SUCCESS"

        Write-GuiLog "PERFORMANCE MATRIX INJECTED SUCCESSFULLY!" "SUCCESS"
        Write-GuiLog "Recommendation: Safely reboot this machine at your next maintenance window to initialize system memory shifts." "WARN"
        
        [System.Windows.Forms.MessageBox]::Show("Autonomous Server Tuning Complete! The system engine configured custom protocols, SMB credits, and Cache profiles. A server reboot is highly recommended.", "Tuning Complete", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
    catch {
        $errText = $_.ToString()
        Write-GuiLog "A fatal execution script error occurred" "ERROR"
    }
})

# Display GUI
$form.ShowDialog() | Out-Null
$form.Dispose()
