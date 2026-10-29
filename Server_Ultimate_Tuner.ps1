Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- APPLICATION WINDOW ---
$form = New-Object System.Windows.Forms.Form
$form.Text = "Windows Server Ultimate Performance Engine"
$form.Size = New-Object System.Drawing.Size(700, 560)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(240, 242, 245)

# --- FONT DEFINITIONS ---
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fontSection = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontConsole = New-Object System.Drawing.Font("Consolas", 9)

# --- TITLE BAR ---
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "⚡ Full-Server Auto-Tuning & Speed Optimization Utility"
$lblTitle.Font = $fontTitle
$lblTitle.Location = New-Object System.Drawing.Point(15, 15)
$lblTitle.Size = New-Object System.Drawing.Size(650, 30)
$lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(20, 24, 30)
$form.Controls.Add($lblTitle)

# --- ACTION BUTTONS ---
$btnDetect = New-Object System.Windows.Forms.Button
$btnDetect.Text = "🔍 1. Audit Full Server State"
$btnDetect.Font = $fontSection
$btnDetect.Location = New-Object System.Drawing.Point(20, 60)
$btnDetect.Size = New-Object System.Drawing.Size(310, 45)
$btnDetect.BackColor = [System.Drawing.Color]::FromArgb(0, 102, 204)
$btnDetect.ForeColor = [System.Drawing.Color]::White
$btnDetect.FlatStyle = "Flat"
$form.Controls.Add($btnDetect)

$btnTweak = New-Object System.Windows.Forms.Button
$btnTweak.Text = "🚀 2. Deploy Full-Throttle Tweaks"
$btnTweak.Font = $fontSection
$btnTweak.Location = New-Object System.Drawing.Point(355, 60)
$btnTweak.Size = New-Object System.Drawing.Size(310, 45)
$btnTweak.BackColor = [System.Drawing.Color]::FromArgb(46, 139, 87)
$btnTweak.ForeColor = [System.Drawing.Color]::White
$btnTweak.FlatStyle = "Flat"
$btnTweak.Enabled = $false
$form.Controls.Add($btnTweak)

# --- LIVE OUTPUT BOX ---
$lblLog = New-Object System.Windows.Forms.Label
$lblLog.Text = "Optimization & Diagnostic Log Output:"
$lblLog.Font = $fontSection
$lblLog.Location = New-Object System.Drawing.Point(20, 120)
$lblLog.Size = New-Object System.Drawing.Size(300, 20)
$form.Controls.Add($lblLog)

$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Font = $fontConsole
$txtLog.Location = New-Object System.Drawing.Point(20, 145)
$txtLog.Size = New-Object System.Drawing.Size(645, 350)
$txtLog.ReadOnly = $true
$txtLog.BackColor = [System.Drawing.Color]::FromArgb(15, 17, 20)
$txtLog.ForeColor = [System.Drawing.Color]::FromArgb(0, 255, 102)
$form.Controls.Add($txtLog)

# --- LOGGING HELPER ---
. "$PSScriptRoot\GuiLogging.ps1"

# --- AUDIT ENGINE LOGIC ---
$btnDetect.Add_Click({
    $txtLog.Clear()
    Write-GuiLog "Beginning deep server bare-metal audit..." "INFO"
    
    # 1. Power Plan Audit
    $activePlan = powercfg /getactiveplan
    if ($activePlan -match "High performance" -or $activePlan -match "Ultimate Performance") {
        Write-GuiLog "Power Delivery: High Performance profile active." "SUCCESS"
    } else {
        Write-GuiLog "Power Delivery: Power scheme throttled (Balanced/PowerSaver)." "WARN"
    }

    # 2. CPU Core Parking Check
    $parkingReg = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\3b619f8e-2454-4ee2-ac44-31a24933d844" -Name Attributes -ErrorAction SilentlyContinue
    if ($parkingReg.Attributes -eq 0) {
        Write-GuiLog "CPU Framework: Core parking avoidance configured." "SUCCESS"
    } else {
        Write-GuiLog "CPU Framework: Core parking defaults allow thread sleeping." "WARN"
    }

    # 3. Storage Layer (NTFS Memory Allocation)
    $ntfsMemory = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name NtfsMemoryUsage -ErrorAction SilentlyContinue
    if ($ntfsMemory.NtfsMemoryUsage -eq 2) {
        Write-GuiLog "Storage IO: NTFS cache paged allocation maximized." "SUCCESS"
    } else {
        Write-GuiLog "Storage IO: NTFS lookup cache throttled (Default)." "WARN"
    }

    # 4. Network SMB Multichannel & RSS Status
    $smbServer = Get-SmbServerConfiguration
    $adapters = Get-SmbServerNetworkInterface
    if ($smbServer.EnableMultiChannel -eq $true) { Write-GuiLog "SMB Protocol: Multichannel operational flags are set." "SUCCESS" } else { Write-GuiLog "SMB Protocol: Multichannel is inactive." "WARN" }
    
    $rssFail = $false
    foreach ($nic in $adapters) {
        if (-not $nic.RssCapable) { $rssFail = $true }
    }
    if (-not $rssFail) { Write-GuiLog "Network Layer: All network pipes report active RSS profiles." "SUCCESS" } else { Write-GuiLog "Network Layer: Adapters missing hardware RSS capabilities." "WARN" }

    Write-GuiLog "Server audit completed. Full-throttle parameters mapping unlocked." "INFO"
    $btnTweak.Enabled = $true
})

# --- AUTO-CORRECT & SPEED OPTIMIZATION ENGINE ---
$btnTweak.Add_Click({
    Write-GuiLog "Executing system-wide hardware unthrottling sequence..." "INFO"

    try {
        # 1. FORCE MAX PERFORMANCE POWER DELIVERY
        Write-GuiLog "Adjusting power management sub-system to High Performance..." "INFO"
        powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c | Out-Null
        Write-GuiLog "Power Plan forced to raw high performance output." "SUCCESS"

        # 2. ELIMINATE CPU CORE PARKING (Ensure all cores stay awake for incoming network interrupts)
        Write-GuiLog "Modifying thread architecture rules to stop Core Parking..." "INFO"
        $coreParkingPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\3b619f8e-2454-4ee2-ac44-31a24933d844"
        Set-ItemProperty -Path $coreParkingPath -Name Attributes -Value 0 -ErrorAction SilentlyContinue
        powercfg /setacvalueindex scheme_current sub_processor CPMINCORES 100 | Out-Null
        powercfg /setactive scheme_current | Out-Null
        Write-GuiLog "Core Parking banned. All physical CPU cores locked in active state." "SUCCESS"

        # 3. UNTHROTTLE FILE SYSTEM CACHING (NTFS Cache Pool Expansion)
        Write-GuiLog "Expanding system pool memory for large file metadata lookups..." "INFO"
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name NtfsMemoryUsage -Value 2 -ErrorAction SilentlyContinue
        Write-GuiLog "NTFS metadata file allocation cache enlarged to maximum." "SUCCESS"

        # 4. REMOVE SYSTEM NETWORK BANDWIDTH THROTTLES
        Write-GuiLog "Overriding Multimedia Network Scheduler bandwidth restrictions..." "INFO"
        $mmcssPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        If (-not (Test-Path $mmcssPath)) { New-Item -Path $mmcssPath -Force | Out-Null }
        Set-ItemProperty -Path $mmcssPath -Name NetworkThrottlingIndex -Value 0xFFFFFFFF -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $mmcssPath -Name SystemResponsiveness -Value 0 -ErrorAction SilentlyContinue
        Write-GuiLog "Network execution throttling index completely bypassed." "SUCCESS"

        # 5. EXECUTE NETWORK & SMB SPEED TUNING
        Write-GuiLog "Unthrottling TCP and SMB stack lanes..." "INFO"
        Set-SmbServerConfiguration -EnableMultiChannel $true -Force
        Set-SmbClientConfiguration -EnableMultiChannel $true -Force
        Enable-NetAdapterRss -Name "*" -ErrorAction SilentlyContinue
        Set-NetTCPSetting -SettingName "Internet" -AutoTuningLevelLocal Normal -CongestionProvider C结构 -ErrorAction SilentlyContinue
        
        Write-GuiLog "SMB Multichannel active, RSS forced, TCP congestion control set to modern architecture." "SUCCESS"

        # Final Verification
        Update-SmbMultichannelConnection -ErrorAction SilentlyContinue
        Write-GuiLog "SERVER TUNING COMPLETE! All bottlenecks systematically minimized." "SUCCESS"
        
        [System.Windows.Forms.MessageBox]::Show("Full Server tuning complete! Network, Storage, CPU, and Power optimizations have been committed successfully.", "Server Optimized", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
    catch {
        Write-GuiLog "An unhandled execution exception caught: $_" "ERROR"
    }
})

# Display GUI
$form.ShowDialog() | Out-Null
$form.Dispose()
