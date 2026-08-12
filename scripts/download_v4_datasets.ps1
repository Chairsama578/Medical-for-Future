$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force data/raw/uci_har, data/raw/uci_postural, data/raw/upfall, data/raw/bidmc, data/raw/cves, data/raw/mimic4wdb | Out-Null

Invoke-WebRequest "https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip" -OutFile "data/raw/uci_har/uci_har.zip"
Expand-Archive -Force "data/raw/uci_har/uci_har.zip" "data/raw/uci_har"

Invoke-WebRequest "https://archive.ics.uci.edu/static/public/341/smartphone+based+recognition+of+human+activities+and+postural+transitions.zip" -OutFile "data/raw/uci_postural/uci_postural.zip"
Expand-Archive -Force "data/raw/uci_postural/uci_postural.zip" "data/raw/uci_postural"

Write-Host "UCI datasets downloaded. UP-Fall/BIDMC/CVES/MIMIC require their respective download/access procedures."
Write-Host "UP-Fall raw sensor dataset is not automatically downloadable from the historical Challenge UP page. Acquire the original dataset manually from an authorized/verified source, then place it under data/raw/upfall/."
