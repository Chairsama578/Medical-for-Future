| Dataset | Branch | Main use | Access |
|---|---|---|---|
| UCI HAR 240 | Activity | walking/sitting/standing/laying | Open |
| UCI 341 | Activity + transitions | raw IMU + posture transitions | Open |
| UP-Fall | Fall | wearable fall vs ADL | Public |
| PhysioNet CVES | Physiology research | stroke-population vs controls, BP/ECG/accelerometer | Open, ~173.9GB |
| PhysioNet BIDMC | Physiology signal validation | PPG/ECG/HR/SpO2 | Open |
| MIMIC-IV Waveform | Physiology expansion | ECG/PPG/BP + clinical linkage | Credentialed |

These sources are not one synchronized multimodal dataset. Train each branch
from the appropriate source, then fuse outputs at runtime. Results are not
clinical validation.
