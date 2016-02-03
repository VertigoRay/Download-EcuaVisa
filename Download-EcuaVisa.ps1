$plex = '\\plex\Media'
$plex_tv_ecuavisa = "${plex}\TV\EcuaVisa"

$noticieros_anteriores = 'http://www.ecuavisa.com/noticieros-anteriores'
$noticieros_episode = 'http://www.ecuavisa.com/ajax-noticiero/nojs/{0}/ampliado'
$number_of_episodes_to_keep = 25

$log = "${plex}\Download-EcuaVisa.log"
$stdout = "${plex}\Download-EcuaVisa.stdout"
$stderr = "${plex}\Download-EcuaVisa.stderr"

###############################################################################

Write-Output '------------' | Out-File $log -Append
Write-Output "Get-Location: $(Get-Location)" | Out-File $log -Append

Push-Location $plex
Write-Output "Get-Location: $(Get-Location)" | Out-File $log -Append

$you_get = Resolve-Path 'you-get-0.4.266-win32.exe'
Write-Output "You_Get: ${you_get}" | Out-File $log -Append

Pop-Location
Write-Output "Get-Location: $(Get-Location)" | Out-File $log -Append

Write-Output "Noticieros Anteriores: ${noticieros_anteriores}" | Out-File $log -Append
Write-Output "Noticieros Episode: ${noticieros_episode}" | Out-File $log -Append

try {
    $html = (Invoke-WebRequest $noticieros_anteriores -UseBasicParsing).Content
} catch {
    Write-Output "[$($_.Exception.GetType().FullName)] $($_.Exception.Message)" | Out-File $log -Append
}

$episode_numbers = [regex]::matches($html, 'ajax\-noticiero\/nojs\/([^\/]+)\/ampliado', 'IgnoreCase') | %{ [int]$_.Groups[1].Value } | sort -Unique -Descending

foreach ($i in 0..($number_of_episodes_to_keep-1)) {
    $episode_url = $noticieros_episode -f $episode_numbers[$i]
    Write-Output "Episode URL (initial): ${episode_url}" | Out-File $log -Append
    try {
        $html = (Invoke-WebRequest $episode_url -UseBasicParsing).Content
    } catch {
        Write-Output "[$($_.Exception.GetType().FullName)] $($_.Exception.Message)" | Out-File $log -Append
    }

    $url = [regex]::matches($html, '<iframe(?:[^>]*)src="([^"]+)"', 'IgnoreCase') | %{ $_.Groups[1].Value }
    Write-Output "Episode URL  (actual): ${url}" | Out-File $log -Append
    $proc = Start-Process -FilePath $you_get -ArgumentList @('--debug', $url) -WorkingDirectory $plex_tv_ecuavisa -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    # you-get errors out while redirecting StdOut
    # Write-Output "Downloading ..." | Out-File $log -Append
    # & "$you_get" --debug "${url}"

    Get-Content $stdout -ErrorAction Ignore | %{ Write-Output "You_Get StdOut: $($_.Trim())" | Out-File $log -Append }
    Write-Output "You_Get Process ($($proc.ID)) Completed [$($proc.ExitCode)] at $($proc.ExitTime): `n$(($proc | Out-String).Trim())" | Out-File $log -Append
    Get-Content $stderr -ErrorAction Ignore | %{ Write-Output "You_Get StdErr: $($_.Trim())" | Out-File $log -Append }
    $stdout, $stderr | Remove-Item -Force -ErrorAction Ignore
}

Write-Output "Looking for Old Episodes to clear out ..." | Out-File $log -Append
$downloaded_episodes = Get-ChildItem $plex_tv_ecuavisa | Sort-Object -Property CreationTime -Descending

foreach ($i in $number_of_episodes_to_keep..999) {
    try { 
        Write-Output "Deleting Old Episode: $($downloaded_episodes[$i].FullName)" | Out-File $log -Append
        Remove-Item $downloaded_episodes[$i].FullName -ErrorAction Stop
    } catch [System.Management.Automation.ParameterBindingValidationException] {
        Write-Output "[$($_.Exception.GetType().FullName)] $($_.Exception.Message)" | Out-File $log -Append
        Write-Output "No more episodes to find. Done checking for Old Episodes!" | Out-File $log -Append
        break
    } catch [System.Management.Automation.ItemNotFoundException] {
        Write-Output "[$($_.Exception.GetType().FullName)] $($_.Exception.Message)" | Out-File $log -Append
        Write-Output "Episode I found a second ago, no longer exists. Moving on ..." | Out-File $log -Append
        continue
    } catch {
        Write-Output "[$($_.Exception.GetType().FullName)] $($_.Exception.Message)" | Out-File $log -Append
        Write-Output "UNHANDLED ERROR: Moving on ..." | Out-File $log -Append
        continue
    }
}
