# Demo flow

1. Start simulator.
2. Sensor packets appear every 200 ms.
3. Linux builds an 8-second rolling window.
4. AI predicts a risk class.
5. SafetyFusion applies temporal persistence.
6. A manual SOS immediately becomes CRITICAL.
7. B.E. FAST symptom confirmation immediately becomes an emergency event.
8. In real UNO Q deployment, the alert is forwarded to the MCU through Bridge.
