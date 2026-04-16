# MITRE ATT&CK Mapping - JWT Abuse

## Adversary Tactics

### Initial Access
- [T1190](https://attack.mitre.org/techniques/T1190/) - Exploit Public-Facing Application

### Execution
- [T1059.003](https://attack.mitre.org/techniques/T1059/003/) - Command Line Interface (Python/PyJWT)

### Persistence
- [T1078.001](https://attack.mitre.org/techniques/T1078/001/) - Valid Accounts: Default Accounts
  - Using forged admin tokens

### Privilege Escalation
- [T1548.002](https://attack.mitre.org/techniques/T1548/002/) - Abuse Elevation Control Mechanism: Bypass User Access Control
  - Via admin claim modification

### Defense Evasion
- [T1027](https://attack.mitre.org/techniques/T1027/) - Obfuscated Files or Information
  - Token encoding as obfuscation

### Credential Access
- [T1040](https://attack.mitre.org/techniques/T1040/) - Network Sniffing
  - Capture JWT tokens in transit

### Lateral Movement
- [T1550.001](https://attack.mitre.org/techniques/T1550/001/) - Use Alternate Authentication Material

## Exploit Toolchain
1. **Detection:** JWT present in Authorization header
2. **Analysis:** PyJWT library decode
3. **Exploitation:** Token forging (none algorithm, brute-force)
4. **Verification:** Successful API access with modified claims
