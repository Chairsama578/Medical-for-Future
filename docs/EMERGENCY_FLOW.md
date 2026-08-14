# Emergency / SOS flow

## Priority

```text
MANUAL SOS
   >
B.E. FAST symptoms
   >
sensor integrity
   >
persistent physiological anomaly ML
   >
normal
```

### Manual SOS
The user presses the physical SOS button or the UI calls `/sos`.
The MCU latches the local alert. The Linux layer records an emergency event.

### B.E. FAST
A caregiver/user can mark:
- balance loss
- eye/vision change
- face drooping
- arm weakness
- speech difficulty

Any active acute symptom is treated as an emergency signal. Record symptom onset time.

### ML
The ML model estimates a **physiological anomaly risk state** from the available sensor features. It is not a stroke diagnosis and should not autonomously call an ambulance. A high-risk persistent output can trigger a local alert and caregiver notification.

For Vietnam, the medical emergency number is 115; 112 is the national emergency number for urgent incidents/rescue coordination. Verify local routing before deploying.
