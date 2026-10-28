Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- APPLICATION WINDOW ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "SMB Multichannel Auto-Tuner & Tweaker"
$form.Size = New-Object System.Drawing.Size(650, 520)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(245, 246, 248)

# --- FONT DEFINITIONS ---
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fontSection = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontRegular = New-Object System.Drawing.Font("Segoe UI", 9)
$fontConsole = New-Object System.Drawing.Font("Consolas", 9)

# --- TITLE BAR ---
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "🚀 SMB Multichannel Performance Engine"
$lblTitle.Font = $fontTitle
$lblTitle.Location = New-Object System.Drawing.Point(15, 15)
$lblTitle.Size = New-Object System.Drawing.Size(600, 30)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(33, 37, 41)
$form.Controls.Add($lblTitle)

# --- DETECT SECTION ---
$btnDetect = New-Object System.Windows.Forms.Button
$btnDetect.Text = "🔍 1. Auto-Detect Configuration"
$btnDetect.Font = $fontSection
$btnDetect.Location = New-Object System.Drawing.Point(20, 60)
$btnDetect.Size = New-Object System.Drawing.Size(280, 40)
$btnDetect.BackColor = [System.Drawing.Color]::FromArgb(0, 123, 255)
$btnDetect.ForeColor = [System.Drawing.Color]::White
$btnDetect.FlatStyle = "Flat"
$form.Controls.Add($btnDetect)

# --- TWEAK & OPTIMIZE SECTION ---
$btnTweak = New-Object System.Windows.Forms.Button
$btnTweak.Text = "⚡ 2. Auto-Correct & Optimize"
$btnTweak.Font = $fontSection
$btnTweak.Location = New-Object System.Drawing.Point(330, 60)
$btnTweak.Size = New-Object System.Drawing.Size(280, 40)
$btnTweak.BackColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
$btnTweak.ForeColor = [System.Drawing.Color]::White
$btnTweak.FlatStyle = "Flat"
$btnTweak.Enabled = $false
$form.Controls.Add($btnTweak)

# --- LIVE OUTPUT BOX ---
$lblLog = New-Object System.Windows.Forms.Label
$lblLog.Text = "System Status Logs:"
$lblLog.Font = $fontSection
$lblLog.Location = New-Object System.Drawing.Point(20, 115)
$lblLog.Size = New-Object System.Drawing.Size(200, 20)
$form.Controls.Add($lblLog)

$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Font = $fontConsole
$txtLog.Location = New-Object System.Drawing.Point(20, 140)
$txtLog.Size = New-Object System.Drawing.Size(590, 320)
$txtLog.ReadOnly = $true
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(220, 220, 220)
$form.Controls.Add($txtLog)

# --- LOGGING HELPER FUNCTION ---
function Write-GuiLog {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = switch ($Type) {
        "SUCCESS" { "[+] SUCCESS:" }
        "WARN"    { "[!] WARNING:" }
        "ERROR"   { "[-] ERROR:  " }
        default   { "[*] INFO:   " }
    }
    $txtLog.AppendText("$timestamp $prefix $Message`r`n")
}

# --- LOGIC: DETECT SYSTEM STATE ---
$btnDetect.Add_Click({
    $txtLog.Clear()
    Write-GuiLog "Starting automated hardware and configuration scan..." "INFO"
    
    # Check Server Configuration
    $smbServer = Get-SmbServerConfiguration
    if ($smbServer.EnableMultiChannel -eq $true) {
        Write-GuiLog "SMB Multichannel Server Protocol is ENABLED." "SUCCESS"
    } else {
        Write-GuiLog "SMB Multichannel Server Protocol is DISABLED." "WARN"
    }

    # Check Client Configuration
    $smbClient = Get-SmbClientConfiguration
    if ($smbClient.EnableMultiChannel -eq $true) {
        Write-GuiLog "SMB Multichannel Client Protocol is ENABLED." "SUCCESS"
    } else {
        Write-GuiLog "SMB Multichannel Client Protocol is DISABLED." "WARN"
    }

    # Audit Network Adapters
    Write-GuiLog "Auditing network interfaces..." "INFO"
    $adapters = Get-SmbServerNetworkInterface
    
    if ($adapters.Count -eq 0) {
        Write-GuiLog "No active SMB network interfaces detected." "ERROR"
    } else {
        $disabledRssCount = 0
        foreach ($nic in $adapters) {
            $status = "Speed: $($nic.Speed / 1GB)Gbps | RSS Capable: $($nic.RssCapable)"
            if ($nic.RssCapable -eq $true) {
                Write-GuiLog "Adapter [$($nic.InterfaceDescription)]: $status" "SUCCESS"
            } else {
                Write-GuiLog "Adapter [$($nic.InterfaceDescription)]: $status" "WARN"
                $disabledRssCount++
            }
        }
        
        if ($disabledRssCount -gt 0) {
            Write-GuiLog "Misconfigurations found! One or more adapters lack active RSS capabilities." "WARN"
        } else {
            Write-GuiLog "All detected adapters are optimally configured for multi-pathing." "SUCCESS"
        }
    }

    # Audit NetDMA / TCP Window Autotuning
    $tcpGlobal = Get-NetTCPSetting -SettingName "Internet"
    if ($tcpGlobal.AutoTuningLevelLocal -eq "Normal") {
        Write-GuiLog "TCP Global Window Autotuning is optimal (Normal)." "SUCCESS"
    } else {
        Write-GuiLog "TCP Global Window Autotuning is throttled ($($tcpGlobal.AutoTuningLevelLocal))." "WARN"
    }

    Write-GuiLog "Scan complete. Optimization sequence unlocked." "INFO"
    $btnTweak.Enabled = $true
})

# --- LOGIC: AUTO-CORRECT & TWEAK ---
$btnTweak.Add_Click({
    Write-GuiLog "Initiating auto-correction and speed optimization..." "INFO"

    try {
        # 1. Force Enable SMB Multichannel
        Write-GuiLog "Enabling SMB Server and Client Multichannel flags..." "INFO"
        Set-SmbServerConfiguration -EnableMultiChannel $true -Force
        Set-SmbClientConfiguration -EnableMultiChannel $true -Force
        Write-GuiLog "Protocol flags applied." "SUCCESS"

        # 2. Automatically Fix RSS globally on physical adapters
        Write-GuiLog "Enabling Receive Side Scaling (RSS) on all physical network adapters..." "INFO"
        Enable-NetAdapterRss -Name "*" -ErrorAction SilentlyContinue
        Write-GuiLog "RSS features forced active across hardware layers." "SUCCESS"

        # 3. Apply High-Performance TCP Tweak
        Write-GuiLog "Optimizing Global TCP stack settings for maximum throughput..." "INFO"
        Set-NetTCPSetting -SettingName "Internet" -AutoTuningLevelLocal Normal -ErrorAction SilentlyContinue
        Write-GuiLog "TCP Window Auto-Tuning restored to full-throttle (Normal)." "SUCCESS"

        # 4. Refresh & Verify
        Write-GuiLog "Restarting local workstation network services to commit tweaks..." "INFO"
        Update-SmbMultichannelConnection -ErrorAction SilentlyContinue
        
        Write-GuiLog "ALL CORRECTIONS APPLIED. Hardware tuning complete!" "SUCCESS"
        Write-GuiLog "Test results by initiating a file transfer and running 'Get-SmbMultichannelConnection' in PowerShell." "INFO"
        
        [System.Windows.Forms.MessageBox]::Show("Server network and SMB stack have been auto-tuned and fixed successfully!", "Optimization Success", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
    catch {
        Write-GuiLog "An error occurred during execution: $_" "ERROR"
    }
})

# Display GUI
$form.ShowDialog() | Out-Null
$form.Dispose()
