[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)
& "$PSScriptRoot\dev_mlh_mcp_server.exe" @Args
