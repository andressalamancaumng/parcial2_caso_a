$doc = Read-Host "Document number (ej: 1234)"
$pw = Read-Host "Password" -AsSecureString
$pwPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pw))
$loginBody = @{ document_number = $doc; password = $pwPlain } | ConvertTo-Json
Write-Host "Logging in..."
$loginResp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
if ($null -eq $loginResp) { Write-Error "No response from login"; exit }
if ($loginResp.mfa_required -ne $true) {
  Write-Host "MFA not required. Received access_token:"
  $loginResp.access_token
  exit
}
Write-Host "nSession token (valid for a short time):" $loginResp.session_token $otp = Read-Host "Paste the OTP (6 dígitos) from your authenticator NOW" $verifyBody = @{ session_token = $loginResp.session_token; otp_code = $otp } | ConvertTo-Json Write-Host "Verifying OTP..." try {   $verify = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/mfa/verify" -Method Post -Body $verifyBody -ContentType "application/json" -TimeoutSec 20   Write-Host "nSuccess. Access token:"
  $verify.access_token
} catch {
  Write-Error "Verify failed:"
  $resp = $.Exception.Response
  if ($resp) {
    $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
    Write-Host $sr.ReadToEnd()
  } else {
    $ | Out-String
  }
}