# Deployment checklist

## PC / VS Code
- Python 3.11+
- create venv
- install requirements
- generate/train/evaluate
- run simulator

## UNO Q
- update board software/firmware
- verify `systemctl status arduino-router`
- flash MCU sketch
- verify `get_device_status` via Linux client
- copy project to `/opt/strokeguard`
- create service user
- install Python dependencies
- start systemd service

## Before real sensors
- exact sensor part numbers
- electrical voltage compatibility
- I2C/SPI addresses
- sampling rates
- sensor placement
- motion artifacts
- PPG signal quality
- BP module validation
- battery profile
- buzzer/LED behavior
- SOS button debounce
- Bridge latency

## Before any public/medical claim
- replace synthetic data
- obtain appropriately labeled, de-identified data
- subject-level train/validation/test split
- avoid data leakage
- evaluate sensitivity/specificity, ROC-AUC, PR-AUC
- test false alarm rate
- test subgroup performance
- external validation
- clinician review
- regulatory/safety review
