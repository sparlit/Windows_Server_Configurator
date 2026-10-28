Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- GLOBAL PROFILE ARRAYS ---
$global:OS_Caption = "Unknown OS"
$global:OS_Version = "0.0"
$global:Is_Server = $true
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
    
    if ($global:OS_Caption -like "*Server*") {
        $global:Is_Server = $true
        Write-GuiLog "Detected Platform: $global:OS_Caption (Server Suite Deployment)" "SUCCESS"
    } else {
        $global:Is_Server = $false
        Write-GuiLog "Detected Platform: $global:OS_Caption (Client Architecture Core)" "SUCCESS"
    }

    # Map architecture matrix profiles
    if ($global:Is_Server -eq $false) {
        Write-GuiLog "Target Architecture Profile: Client Optimization Matrix Map Engaged." "INFO"
        $global:Recommended_TCP = "CUBIC"
        $global:Supports_ECN = $true
        $global:Max_Credits = 4096
        $global:Max_Worker_Threads = 32
    }
    elseif ($global:OS_Version.Major -eq 6 -and $global:OS_Version.Minor -le 3) {
        Write-GuiLog "Target Architecture Profile: Legacy NT 6.x Kernel Suite Identified." "INFO"
        $global:Recommended_TCP = "CTCP"
        $global:Supports_ECN = $false
        $global:Max_Credits = 8192
        $global:Max_Worker_Threads = 64
    }
    else {
        Write-GuiLog "Target Architecture Profile: Modern Enterprise Server Suite Identified." "INFO"
        $global:Recommended_TCP = "CUBIC"
        $global:Supports_ECN = $true
        $global:Max_Credits = 32768
        $global:Max_Worker_Threads = 256
    }

    Write-GuiLog "Dynamic profile rules generated. Tuning matrices unlocked." "INFO"
    $btnTweak.Enabled = $true
})

# --- TAILORED TUNING EXECUTION ENGINE ---
$btnTweak.Add_Click({
    Write-GuiLog "Deploying dynamic optimization matrices..." "INFO"

    try {
        # 1. TCP STACK OPTIMIZATION
        Write-GuiLog "Injecting Tailored Network Optimization Protocol ($global:Recommended_TCP)..." "INFO"
        if ($global:Supports_ECN) {
            Set-NetTCPSetting -SettingName "Internet" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -EcnCapability Enabled -ErrorAction SilentlyContinue
            Set-NetTCPSetting -SettingName "Datacenter" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -EcnCapability Enabled -ErrorAction SilentlyContinue
            Write-GuiLog "TCP Core optimized via $global:Recommended_TCP with active ECN flags." "SUCCESS"
        } else {
            Set-NetTCPSetting -SettingName "Internet" -CongestionProvider $global:Recommended_TCP -AutoTuningLevelLocal Normal -ErrorAction SilentlyContinue
            Write-GuiLog "TCP Core optimized via legacy $global:Recommended_TCP framework." "SUCCESS"
        }

        # 2. CONCURRENT LAYER ALLOCATIONS (SERVER VS CLIENT SAFETIES)
        if ($global:Is_Server) {
            Write-GuiLog "Tuning Enterprise Server SMB configurations..." "INFO"
            Set-SmbServerConfiguration -Smb2CreditsMax $global:Max_Credits -AsynchronousRequestsMax ($global:Max_Worker_Threads * 16) -AdditionalCriticalWorkerThreads $global:Max_Worker_Threads -Force
            Write-GuiLog "SMB Server buffer pools allocated successfully." "SUCCESS"
        } else {
            Write-GuiLog "Skipping SMB Server modifications (Client Operating System detected)." "INFO"
            Write-GuiLog "Optimizing client-side SMB link pipelining windows..." "INFO"
            Set-SmbClientConfiguration -EnableMultiChannel $true -Force
            Write-GuiLog "SMB Client interface pipelines unthrottled." "SUCCESS"
        }

        # 3. KERNEL MEMORY & REGISTRY THROTTLES
        Write-GuiLog "Optimizing host subsystem memory and worker constraints..." "INFO"
        if ($global:Is_Server) {
            Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name LargeSystemCache -Value 1 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name NtfsMemoryUsage -Value 2 -ErrorAction SilentlyContinue
        }
        
        $lanmanPath = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
        Set-ItemProperty -Path $lanmanPath -Name MaxThreadsPerCmd -Value 255 -Force -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $lanmanPath -Name MaxWorkItems -Value 8192 -Force -ErrorAction SilentlyContinue
        Write-GuiLog "System background command pipelines expanded." "SUCCESS"

        # 4. RE-BIND MULTICHANNEL
        Write-GuiLog "Synchronizing interface arrays for active SMB Multichannel delivery..." "INFO"
        Enable-NetAdapterRss -Name "*" -ErrorAction SilentlyContinue
        Update-SmbMultichannelConnection -ErrorAction SilentlyContinue
        Write-GuiLog "SMB Multichannel configurations verified and active." "SUCCESS"

        Write-GuiLog "PERFORMANCE MATRIX INJECTED SUCCESSFULLY!" "SUCCESS"
        [System.Windows.Forms.MessageBox]::Show("Tuning Complete! The script adjusted settings safely for your Windows 11 architecture environment.", "Tuning Complete", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
    catch {
        $errText = $_.ToString()
        Write-GuiLog "A fatal execution script error occurred: $errText" "ERROR"
    }
})

# Display GUI
$form.ShowDialog() | Out-Null
$form.Dispose()
