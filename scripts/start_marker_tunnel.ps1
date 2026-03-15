Write-Host "Opening Marker tunnel to moslabserver..."
Write-Host "Keep this window open. Ctrl+C to stop tunnel."
Write-Host ""
ssh -N -L 8001:localhost:8001 xyzxyzserver
