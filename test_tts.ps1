# Test TTS endpoint
$body = @{text="Hello world"; speed="0.9"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/ai/tts/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response keys:" ($response | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name)
Write-Host "Audio data length:" $response.audio_data.Length
