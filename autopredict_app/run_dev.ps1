# AutoPredict dev runner
# Forwards PC ports to the Android device so localhost works in the Flutter app

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"

Write-Host "Setting up adb reverse port forwarding..." -ForegroundColor Cyan
& $adb reverse tcp:8000 tcp:8000
& $adb reverse tcp:11434 tcp:11434
& $adb reverse --list

Write-Host "`nStarting flutter run..." -ForegroundColor Green
flutter run
