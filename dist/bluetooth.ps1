<#
.SYNOPSIS
Enables or disables Bluetooth radio with proper feedback.

.DESCRIPTION
This script provides reliable Bluetooth control using Windows Runtime APIs with clear status messages.

.PARAMETER BluetoothStatus
Specifies whether to turn Bluetooth On or Off
#>

[CmdletBinding()]
Param (
    [Parameter(Mandatory=$true)]
    [ValidateSet('Off', 'On')]
    [string]$BluetoothStatus
)

# Ensure Bluetooth Support Service is running
try {
    $btService = Get-Service bthserv -ErrorAction Stop
    if ($btService.Status -ne 'Running') {
        Write-Host "Starting Bluetooth Support Service..."
        Start-Service bthserv -ErrorAction Stop
        Start-Sleep -Seconds 2  # Allow service to initialize
    }
}
catch {
    Write-Warning "Failed to start Bluetooth Support Service: $_"
    exit 1
}

# Load required Windows Runtime assemblies
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $null = [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]
    $null = [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime]
}
catch {
    Write-Warning "Failed to load required assemblies: $_"
    exit 1
}

# Create async task helper function
Function Await-WinRTAsyncTask {
    param(
        [object]$WinRtTask,
        [Type]$ResultType
    )
    
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | 
        Where-Object { 
            $_.Name -eq 'AsTask' -and 
            $_.GetParameters().Count -eq 1 -and 
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
        })[0]

    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}

# Main execution
try {
    Write-Host "Requesting Bluetooth radio access..."
    $accessStatus = Await-WinRTAsyncTask -WinRtTask ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) -ResultType ([Windows.Devices.Radios.RadioAccessStatus])
    
    if ($accessStatus -ne 'Allowed') {
        Write-Warning "Access to Bluetooth radio was denied by system"
        exit 1
    }

    Write-Host "Getting available radios..."
    $radios = Await-WinRTAsyncTask -WinRtTask ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) -ResultType ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
    $bluetoothRadio = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }

    if (-not $bluetoothRadio) {
        Write-Warning "No Bluetooth radio found on this system"
        exit 1
    }

    Write-Host "Current Bluetooth state: $($bluetoothRadio.State)"
    Write-Host "Attempting to set Bluetooth to: $BluetoothStatus..."
    
    $result = Await-WinRTAsyncTask -WinRtTask ($bluetoothRadio.SetStateAsync($BluetoothStatus)) -ResultType ([Windows.Devices.Radios.RadioAccessStatus])
    
    if ($result -eq 'Allowed') {
        Write-Host "Successfully set Bluetooth to $BluetoothStatus"
        exit 0
    }
    else {
        Write-Warning "Failed to change Bluetooth state. Access status: $result"
        exit 1
    }
}
catch {
    Write-Warning "An unexpected error occurred: $_"
    exit 1
}