# 🔐 Persay - Privacy & Security Design Document

**Version:** 1.0  
**Last Updated:** November 2025  
**Classification:** Internal Documentation

---

## 1. Application Overview

### What Persay Does
Persay is an **end-to-end encrypted messaging application** for secure private communications between users.

| Aspect | Details |
|--------|---------|
| **App Type** | End-to-end encrypted messaging application |
| **Target Users** | Adults 18+ only |
| **Platforms** | Web app (initial), iOS/Android (planned) |
| **Encryption** | AES-256-GCM with PBKDF2 key derivation |
| **Architecture** | Client-side encryption, server relay |

### Core Principle
> **Zero-Knowledge Architecture**: The server NEVER has access to unencrypted message content or user encryption keys.

---

## 2. Data Collection Inventory

### 2.1 Data We Collect

| Data Type | Collected | Purpose | Retention | Legal Basis (GDPR) |
|-----------|-----------|---------|-----------|-------------------|
| **Username** | ✅ Yes | Account identification | Until account deletion | Contract |
| **Password Hash** | ✅ Yes | Authentication | Until account deletion | Contract |
| **Encrypted Messages** | ✅ Yes | Message delivery | Until user deletes | Contract |
| **Message Metadata** | ⚠️ Minimal | Delivery routing | 30 days | Legitimate Interest |
| **IP Address** | ⚠️ Minimal | Security/abuse prevention | 7 days | Legitimate Interest |
| **Device Info** | ❌ No | - | - | - |
| **Location** | ❌ No | - | - | - |
| **Contacts** | ❌ No | - | - | - |
| **Phone Number** | ❌ No | - | - | - |
| **Email** | ❌ No (optional future) | - | - | - |
| **Payment Data** | ❌ No | - | - | - |

### 2.2 Data We NEVER Collect or Access

- ❌ Unencrypted message content
- ❌ User encryption keys
- ❌ Contact lists or address books
- ❌ Location data
- ❌ Biometric data
- ❌ Financial information
- ❌ Third-party tracking data

### 2.3 Metadata Minimization

```
WHAT WE STORE (encrypted):           WHAT WE DON'T STORE:
├── Encrypted message blob           ├── Message content
├── Sender username                  ├── Encryption keys
├── Recipient username               ├── IP addresses (>7 days)
├── Timestamp                        ├── Device fingerprints
└── Salt (for decryption)            └── Read receipts
```

---

## 3. User Demographics & Age Restrictions

### 3.1 Age Requirements

| Jurisdiction | Minimum Age | Enforcement |
|--------------|-------------|-------------|
| **United States** | 18+ | Age gate, ToS |
| **European Union** | 18+ | Age gate, ToS |
| **United Kingdom** | 18+ | Age gate, ToS |
| **Global Default** | 18+ | Age gate, ToS |

### 3.2 COPPA Compliance (US)

**Status:** ✅ Compliant by Design

- App is NOT directed at children under 13
- App is NOT directed at users under 18
- Clear age gate requiring users to confirm they are 18+
- Terms of Service explicitly prohibit users under 18
- No collection of data known to be from minors

### 3.3 GDPR Article 8 Compliance (EU)

**Status:** ✅ Compliant by Design

- Minimum age set to 18 (above EU requirements)
- No processing of minor data
- Clear consent mechanisms for adults

---

## 4. Server & Company Location

### 4.1 Infrastructure

| Component | Location | Provider |
|-----------|----------|----------|
| **Application Server** | [To be determined] | [To be determined] |
| **Database** | [To be determined] | [To be determined] |
| **CDN** | [To be determined] | [To be determined] |
| **Company Registration** | [To be determined] | [To be determined] |

### 4.2 Cross-Border Data Transfers

For EU users, if data is processed outside EEA:
- Standard Contractual Clauses (SCCs) in place
- Transfer Impact Assessment completed
- Technical safeguards (E2E encryption) ensure content protection

---

## 5. Monetization Model

### Current Model
| Revenue Source | Status | Privacy Impact |
|----------------|--------|----------------|
| **Advertisements** | ❌ None | No tracking |
| **Data Sales** | ❌ Never | Zero data sharing |
| **Subscriptions** | 🔄 Planned | Minimal payment data |
| **Premium Features** | 🔄 Planned | No additional data |

### Privacy Commitments
- ✅ No selling of user data (CCPA "sale" definition)
- ✅ No sharing of user data with third parties for advertising
- ✅ No behavioral profiling
- ✅ No targeted advertising

---

## 6. Security Architecture

### 6.1 Encryption Implementation

```
┌─────────────────────────────────────────────────────────────┐
│                    ENCRYPTION FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  USER INPUT          KEY DERIVATION         ENCRYPTION      │
│  ───────────         ──────────────         ──────────      │
│                                                             │
│  Password ──────────► PBKDF2 ──────────────► AES-256-GCM    │
│       │               (480,000 iterations)        │         │
│       │                      │                    │         │
│       ▼                      ▼                    ▼         │
│  Random Salt ────────► 256-bit Key ──────► Ciphertext      │
│  (16 bytes)                                 + Auth Tag      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Cryptographic Standards

| Component | Standard | Implementation |
|-----------|----------|----------------|
| **Symmetric Encryption** | AES-256-GCM | `cryptography` library (Fernet) |
| **Key Derivation** | PBKDF2-HMAC-SHA256 | 480,000 iterations |
| **Random Generation** | CSPRNG | `os.urandom()` |
| **Transport Security** | TLS 1.3 | Server configuration |
| **Password Storage** | bcrypt | (planned) |

### 6.3 Key Management

| Principle | Implementation |
|-----------|----------------|
| **Key Generation** | Client-side only |
| **Key Storage** | Never on server |
| **Key Transmission** | Never transmitted |
| **Key Rotation** | User-initiated password change |

### 6.4 Security Measures

- ✅ End-to-end encryption (content never visible to server)
- ✅ TLS for all network communications
- ✅ No plaintext storage of passwords
- ✅ Minimal logging (no message content)
- ✅ Rate limiting on authentication
- ✅ CSRF protection
- ✅ Secure session management

---

## 7. User Rights Implementation

### 7.1 Rights Summary

| Right | GDPR | CCPA | Implementation |
|-------|------|------|----------------|
| **Access** | Art. 15 | ✅ | Export endpoint |
| **Deletion** | Art. 17 | ✅ | Delete account feature |
| **Portability** | Art. 20 | - | Data export (JSON) |
| **Rectification** | Art. 16 | ✅ | Profile edit |
| **Opt-out of Sale** | - | ✅ | N/A (no sales) |
| **Non-discrimination** | - | ✅ | Equal service |

### 7.2 Technical Implementation

```python
# Required endpoints/features:
POST /api/user/export          # Export all user data
POST /api/user/delete          # Delete account & all data
PUT  /api/user/profile         # Correct user data
GET  /api/user/privacy-settings # View privacy choices
PUT  /api/user/privacy-settings # Update privacy choices
```

### 7.3 Deletion Process

When a user requests account deletion:
1. ✅ Delete username and auth credentials
2. ✅ Delete all encrypted message data
3. ✅ Delete all metadata associated with user
4. ⚠️ Retain minimal security logs (anonymized) for 30 days
5. ✅ Confirm deletion to user

---

## 8. Law Enforcement & Legal Requests

### 8.1 What We CAN Provide (with valid legal process)

| Data Type | Availability |
|-----------|--------------|
| Username | ✅ Yes |
| Account creation date | ✅ Yes |
| Last login timestamp | ✅ Yes |
| IP address (last 7 days) | ⚠️ Limited |

### 8.2 What We CANNOT Provide (by design)

| Data Type | Reason |
|-----------|--------|
| Message content | E2E encrypted, we don't have keys |
| Encryption keys | Never stored on server |
| Contact lists | Not collected |
| Location history | Not collected |

### 8.3 Transparency Commitment

- Publish transparency reports (when applicable)
- Notify users of legal requests where legally permitted
- No backdoors in encryption - ever

---

## 9. Export Control Compliance

### 9.1 US Export Administration Regulations (EAR)

| Classification | Details |
|----------------|---------|
| **ECCN** | 5D002 (encryption software) |
| **License Exception** | ENC (mass-market encryption) |
| **Reporting** | Self-classification maintained |

### 9.2 Restricted Destinations

The following countries/regions are blocked per OFAC sanctions:
- Cuba
- Iran
- North Korea
- Syria
- Crimea region
- [Others per current OFAC SDN list]

### 9.3 EU Dual-Use Regulation (2021/821)

- Standard consumer encryption: generally exempt
- No surveillance capabilities included
- Internal compliance procedures documented

---

## 10. Incident Response Plan

### 10.1 Breach Classification

| Severity | Criteria | Response Time |
|----------|----------|---------------|
| **Critical** | Encryption keys compromised | Immediate |
| **High** | User credentials exposed | 24 hours |
| **Medium** | Metadata exposed | 72 hours |
| **Low** | Service disruption | Best effort |

### 10.2 Notification Requirements

| Jurisdiction | Authority | Timeline | Users |
|--------------|-----------|----------|-------|
| **EU/EEA** | Supervisory Authority | 72 hours | Without undue delay |
| **California** | CA AG (if >500 users) | Expedient | Without unreasonable delay |
| **Other US States** | Varies | Varies | Varies |

### 10.3 Breach Response Steps

1. **Contain** - Isolate affected systems
2. **Assess** - Determine scope and data affected
3. **Document** - Record timeline and actions
4. **Notify** - Inform regulators and users as required
5. **Remediate** - Fix vulnerabilities
6. **Review** - Post-incident analysis

---

## 11. Compliance Checklist

### Architecture & Crypto
- [x] Data minimization implemented
- [x] Using standard cryptographic libraries
- [x] No custom/homegrown crypto
- [x] Key management documented
- [x] E2E encryption for all messages

### Legal Documents
- [ ] Privacy Policy (US + EU sections)
- [ ] Terms of Service
- [ ] Cookie Policy (web)
- [ ] Export control notice

### User Rights
- [ ] Data export endpoint
- [ ] Account deletion feature
- [ ] Privacy settings UI
- [ ] Consent management

### Age Verification
- [ ] Age gate on registration
- [ ] ToS age requirement
- [ ] No minor-directed features

### Export Control
- [ ] ECCN classification
- [ ] Geo-blocking for sanctioned countries
- [ ] Export notice in Terms

---

## 12. Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Nov 2025 | Initial document |

---

## 13. Contacts

| Role | Contact |
|------|---------|
| **Privacy Questions** | [privacy@persay.app] |
| **Security Issues** | [security@persay.app] |
| **Legal Requests** | [legal@persay.app] |
| **DPO (EU)** | [dpo@persay.app] |

---

*This document should be reviewed and updated whenever significant changes are made to data collection, processing, or the application architecture.*

