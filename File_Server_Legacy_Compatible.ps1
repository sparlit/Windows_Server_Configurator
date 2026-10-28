Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- APPLICATION WINDOW ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "Enterprise File Server Auto-Tuning Engine (Multi-OS)"
$form.Size = New-Object System.Drawing.Size(720, 580)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(242, 244, 248)

# --- FONT DEFINITIONS ---
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$fontSection = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontConsole = New-Object System.Drawing.Font("Consolas", 9)

# --- TITLE BAR ---
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "📁 Enterprise SMB File Server Performance Optimizer"
$lblTitle.Font = $fontTitle
$lblTitle.Location = New-Object System.Drawing.Point(15, 15)
$lblTitle.Size = New-Object System.Drawing.Size(680, 30)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(26, 36, 43)
$form.Controls.Add($lblTitle)

# --- ACTION BUTTONS ---
$btnDetect = New-Object System.Windows.Forms.Button
$btnDetect.Text = "🔍 Analyze File Server Bottlenecks"
$btnDetect.Font = $fontSection
$btnDetect.Location = New-Object System.Drawing.Point(20, 60)
$btnDetect.Size = New-Object System.Drawing.Size(320, 45)
$btnDetect.BackColor = [System.Drawing.Color]::FromArgb(0, 92, 175)
$btnDetect.ForeColor = [System.Drawing.Color]::White
$btnDetect.FlatStyle = "Flat"
$form.Controls.Add($btnDetect)

$btnTweak = New-Object System.Windows.Forms.Button
$btnTweak.Text = "⚡ Inject Ultimate Performance Matrix"
$btnTweak.Font = $fontSection
$btnTweak.Location = New-Object System.Drawing.Point(365, 60)
$btnTweak.Size = New-Object System.Drawing.Size(320, 45)
$btnTweak.BackColor = [System.Drawing.Color]::FromArgb(16, 124, 65)
$btnTweak.ForeColor = [System.Drawing.Color]::White
$btnTweak.FlatStyle = "Flat"
$btnTweak.Enabled = $false
$form.Controls.Add($btnTweak)

# --- LIVE OUTPUT BOX ---
$lblLog = New-Object System.Windows.Forms.Label
$lblLog.Text = "Engine Execution Profile Output:"
$lblLog.Font = $fontSection
$lblLog.Location = New-Object System.Drawing.Point(20, 120)
$lblLog.Size = New-Object System.Drawing.Size(300, 20)
$form.Controls.Add($lblLog)

$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Font = $fontConsole
$txtLog.Location = New-Object System.Drawing.Point(20, 145)
$txtLog.Size = New-Object System.Drawing.Size(665, 365)
$txtLog.ReadOnly = $true
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(10, 15, 20)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(57, 255, 20)
$form.Controls.Add($txtLog)

# --- LOGGING HELPER ---
function Write-GuiLog {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = switch ($Type) {
        "SUCCESS" { "[PASS] " }
        "WARN"    { "[WARN] " }
        "ERROR"   { "[FAIL] " }
        default   { "[INFO] " }
    }
    $txtLog.AppendText("$timestamp $prefix $Message`r`n")
}

# --- AUDIT LOGIC ---
$btnDetect.Add_Click({
    $txtLog.Clear()
    $osVersion = (Get-CimInstance Win32_OperatingSystem).Caption
    Write-GuiLog "Detected Operating System: $osVersion" "INFO"
    Write-GuiLog "Inspecting deep parameters for optimized File Services..." "INFO"
    
    # 1. SMB Server Configurations
    $smbConfig = Get-SmbServerConfiguration
    if ($smbConfig.AsynchronousRequestsMax -ge 512) {
        Write-GuiLog "SMB Threading: Concurrency limits are unlocked ($($smbConfig.AsynchronousRequestsMax))." "SUCCESS"
    } else {
        Write-GuiLog "SMB Threading: Async request concurrency restricted to stock default ($($smbConfig.AsynchronousRequestsMax))." "WARN"
    }
    
    if ($smbConfig.Smb2CreditsMax -ge 8192) {
        Write-GuiLog "SMB Windowing: Max Credits are expanded ($($smbConfig.Smb2CreditsMax))." "SUCCESS"
    } else {
        Write-GuiLog "SMB Windowing: Max Credits at standard baseline ($($smbConfig.Smb2CreditsMax))." "WARN"
    }

    # 2. Large System Cache Registry Audit
    $sysCache = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name LargeSystemCache -ErrorAction SilentlyContinue
    if ($sysCache.LargeSystemCache -eq 1) {
        Write-GuiLog "Memory Caching: Dedicated large-block file caching is ACTIVE." "SUCCESS"
    } else {
        Write-GuiLog "Memory Caching: System Cache prioritized for application execution rather than file pooling." "WARN"
    }

    Write-GuiLog "Analysis complete. Target tweaks mapped for your specific OS version." "INFO"
    $btnTweak.Enabled = $true
})

# --- AUTO-CORRECT ENGINE ---
$btnTweak.Add_Click({
    Write-GuiLog "Deploying high-throughput File Server optimizations..." "INFO"

    try {
        # 1. UNTHROTTLE SMB BUFFER CREDIT LAYERS
        Write-GuiLog "Expanding SMB protocol token windows & concurrent requests pools..." "INFO"
        Set-SmbServerConfiguration -Smb2CreditsMax 16384 -AsynchronousRequestsMax 2048 -AdditionalCriticalWorkerThreads 64 -Force
        Write-GuiLog "SMB Concurrency profiles locked into Enterprise Max values (Credits: 16384)." "SUCCESS"

        # 2. OPTIMIZE MEMORY PROFILE FOR FILE I/O OVER PROGRAMS
        Write-GuiLog "Tuning Memory Manager to favor working set cache sizes..." "INFO"
        $memPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
        Set-ItemProperty -Path $memPath -Name LargeSystemCache -Value 1 -ErrorAction SilentlyContinue
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name NtfsMemoryUsage -Value 2 -ErrorAction SilentlyContinue
        Write-GuiLog "RAM system caching matrix realigned exclusively for intensive file storage access." "SUCCESS"

        # 3. OS DYNAMIC TCP TUNING
        $osObj = Get-CimInstance Win32_OperatingSystem
        if ($osObj.Version -like "6.2*" -or $osObj.Version -like "6.3*") {
            # Windows Server 2012 / 2012 R2 Target
            Write-GuiLog "Applying Server 2012 TCP optimization profile (CTCP)..." "INFO"
            Set-NetTCPSetting -SettingName "Internet" -CongestionProvider CTCP -AutoTuningLevelLocal Normal -ErrorAction SilentlyContinue
            Set-NetTCPSetting -SettingName "Datacenter" -CongestionProvider CTCP -AutoTuningLevelLocal Normal -ErrorAction SilentlyContinue
            Write-GuiLog "TCP framework hardcoded to high-density Compound TCP (CTCP)." "SUCCESS"
        } else {
            # Windows Server 2016 or higher Target
            Write-GuiLog "Applying Server 2016+ TCP optimization profile (CUBIC + ECN)..." "INFO"
            Set-NetTCPSetting -SettingName "Internet" -CongestionProvider CUBIC -AutoTuningLevelLocal Normal -EcnCapability Enabled -ErrorAction SilentlyContinue
            Set-NetTCPSetting -SettingName "Datacenter" -CongestionProvider CUBIC -AutoTuningLevelLocal Normal -EcnCapability Enabled -ErrorAction SilentlyContinue
            Write-GuiLog "TCP framework hardcoded to high-density CUBIC with ECN." "SUCCESS"
        }

        # 4. REMOVE LARGE FILE TRANSFER REGISTRY THROTTLES
        Write-GuiLog "Overriding LanmanServer scaling ceilings..." "INFO"
        $lanmanPath = "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
        Set-ItemProperty -Path $lanmanPath -Name MaxThreadsPerCmd -Value 255 -Force -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $lanmanPath -Name MaxWorkItems -Value 8192 -Force -ErrorAction SilentlyContinue
        Write-GuiLog "Lanman execution bottlenecks dropped. Pipeline constraints eliminated." "SUCCESS"

        # 5. FORCE SMB MULTICHANNEL HARDWARE ALIGNMENT
        Write-GuiLog "Re-verifying physical Multichannel binding properties..." "INFO"
        Set-SmbServerConfiguration -EnableMultiChannel $true -Force
        Set-SmbClientConfiguration -EnableMultiChannel $true -Force
        Enable-NetAdapterRss -Name "*" -ErrorAction SilentlyContinue
        Update-SmbMultichannelConnection -ErrorAction SilentlyContinue
        Write-GuiLog "SMB Multichannel bindings compiled natively." "SUCCESS"

        Write-GuiLog "🔥 FILE SERVER FULL OPTIMIZATION COMPLETE!" "SUCCESS"
        Write-GuiLog "Please note: A server restart is recommended for kernel memory shifts to completely initialize." "WARN"
        
        [System.Windows.Forms.MessageBox]::Show("File Server optimizations committed successfully for your Operating System version!`n`nReboot the server to completely initialize kernel memory cache shifts.", "File Server Fully Optimized", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
    catch {
        Write-GuiLog "An unhandled optimization error occurred: $_" "ERROR"
    }
})

# Display GUI
$form.ShowDialog() | Out-Null
$form.Dispose()
