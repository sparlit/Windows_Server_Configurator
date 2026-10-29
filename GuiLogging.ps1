# --- LOGGING HELPER MODULE ---
function Write-GuiLog {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [string]$Type = "INFO",
        [object]$TextBox = $null
    )
    if ($null -eq $TextBox) {
        $TextBox = Get-Variable -Name "txtLog" -ValueOnly -ErrorAction SilentlyContinue
    }
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = switch ($Type) {
        "SUCCESS" { "[PASS] " }
        "WARN"    { "[WARN] " }
        "ERROR"   { "[FAIL] " }
        default   { "[INFO] " }
    }
    if ($null -ne $TextBox) {
        $TextBox.AppendText("$timestamp $prefix $Message`r`n")
    }
}
