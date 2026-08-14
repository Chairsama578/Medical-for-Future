| Dataset | Branch | Main use | Access |
|---|---|---|---|
| UCI HAR 240 | Activity | walking/sitting/standing/laying | Open |
| UCI 341 | Activity + transitions | raw IMU + posture transitions | Open |
| UP-Fall | Fall | original wearable/ambient/vision research dataset | Manual acquisition; historical Challenge UP files unavailable |
| UMAFall | Current Fall dataset source | acquired under `data/raw/umafall/`; accelerometer + gyroscope; explicit FALL/ADL metadata; raw validation currently blocked by malformed axis rows | Public institutional repository, CC BY-NC 4.0 |
| SisFall | Fall backup candidate | multi-subject IMU falls/ADLs; two accelerometers + gyroscope | Source endpoint requires manual verification |
| UniMiB SHAR | Fall backup candidate | multi-subject smartphone acceleration falls/ADLs | Gyroscope absent; access/license requires verification |
| BIDMC PPG and Respiration | Current physiology demo subset | records 01-05 manually acquired; PPG/ECG/RESP raw + HR/SpO2/RR Numerics | PhysioNet open access, ODC Attribution; full 53-record dataset not downloaded |
| MIMIC-III Waveform | Physiology expansion | ECG/PPG/ABP/RESP and numerics at scale | PhysioNet ODbL; ~6.7 TB, not practical for current demo |
| MIMIC-III-Ext-PPG | Physiology expansion | PPG with ECG/ABP/RESP and derived HR/BP metadata | Credentialed PhysioNet, DUA/training required; not acquired |
| PhysioNet CVES | Physiology research | stroke-population vs controls, BP/ECG/accelerometer | Open, ~173.9GB |
| PhysioNet BIDMC | Physiology signal validation | PPG/ECG/HR/SpO2 | Open |
| MIMIC-IV Waveform | Physiology expansion | ECG/PPG/BP + clinical linkage | Credentialed |

These sources are not one synchronized multimodal dataset. Train each branch
from the appropriate source, then fuse outputs at runtime. Results are not
clinical validation.
