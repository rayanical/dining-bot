# Test script for chat endpoint
# Usage: .\test_chat.ps1

$body = @{
    query = "Where's the best vegan protein at Worcester?"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
        -Method POST `
        -Headers $headers `
        -Body $body
    
    Write-Host "Success! Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Make sure the backend is running on http://localhost:8000" -ForegroundColor Yellow
}

