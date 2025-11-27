# ⚖️ Persay - Legal Disclaimers & Compliance

**Version:** 1.0  
**Last Updated:** November 2025

---

## 1. Independence Statement

Persay is an **independent, original software product** developed from the ground up. 

### 1.1 No Affiliation
Persay is NOT affiliated with, endorsed by, sponsored by, or in any way officially connected with:
- Any other messaging application or service
- Any social media platform
- Any technology company
- Any government agency

### 1.2 Original Work
All code, designs, and intellectual property in Persay are original works created specifically for this project, or use properly licensed open-source components.

---

## 2. Trademark Notice

### 2.1 Our Trademarks
"Persay" and the Persay logo are trademarks of [Company Name]. 

### 2.2 Third-Party Trademarks
Any third-party trademarks, service marks, or trade names referenced in documentation are the property of their respective owners and are used solely for identification purposes. Such use does not imply endorsement or affiliation.

### 2.3 No Trademark Infringement
We have conducted due diligence to ensure that:
- Our name "Persay" does not infringe existing trademarks in relevant classes
- Our branding and design are original and distinctive
- Our marketing makes no false claims about affiliation with other services

---

## 3. Advertising Standards Compliance

### 3.1 Truthful Claims
All claims made about Persay are factually accurate and verifiable:

| Claim | Verification |
|-------|--------------|
| "End-to-end encrypted" | ✅ Messages are encrypted client-side using AES-256-GCM before transmission |
| "We can't read your messages" | ✅ Server only receives and stores encrypted data; no keys stored server-side |
| "AES-256 encryption" | ✅ Implemented using the `cryptography` library with Fernet (AES-256-GCM) |
| "256-bit key length" | ✅ PBKDF2 derives 256-bit keys from user passwords |

### 3.2 Claims We Avoid (False Advertising Prevention)

We do NOT claim:
- ❌ "Military-grade encryption" (undefined marketing term)
- ❌ "Unbreakable" or "Unhackable" (no system is perfect)
- ❌ "NSA-proof" (unverifiable and potentially misleading)
- ❌ "Bank-level security" (vague comparative claim)
- ❌ "Best encryption" (subjective superlative)
- ❌ User counts or statistics we cannot verify
- ❌ Performance metrics without substantiation
- ❌ Comparisons to competing products

### 3.3 FTC Compliance (US)
Our advertising complies with Federal Trade Commission guidelines:
- No deceptive claims
- No unfair practices
- Clear and conspicuous disclosures
- Substantiation for all claims

### 3.4 EU Unfair Commercial Practices Directive
Our communications comply with EU advertising standards:
- No misleading actions or omissions
- No aggressive commercial practices
- Transparent material information

---

## 4. Encryption Claims - Technical Accuracy

### 4.1 What We Use
| Component | Standard | Implementation |
|-----------|----------|----------------|
| Symmetric Encryption | AES-256-GCM | Python `cryptography` library (Fernet) |
| Key Derivation | PBKDF2-HMAC-SHA256 | 480,000 iterations |
| Random Generation | OS CSPRNG | `os.urandom()` |
| Transport | TLS 1.2+ | Web server configuration |

### 4.2 What We Claim
- **"Industry-standard encryption"** ✅ AES-256 is a NIST-approved standard
- **"256-bit encryption"** ✅ Accurate key length
- **"End-to-end encrypted"** ✅ Encryption/decryption occurs only on user devices

### 4.3 Limitations We Acknowledge
- No encryption system is mathematically proven unbreakable
- Security depends on user practices (password strength, device security)
- Implementation vulnerabilities are possible in any software
- We recommend security-conscious users conduct their own review

---

## 5. Competitive Practices

### 5.1 Fair Competition
We compete fairly in the marketplace:
- No false claims about competitors
- No trademark infringement
- No deceptive comparative advertising
- No misappropriation of trade secrets

### 5.2 No Disparagement
We do not:
- Make false statements about competing products
- Imply competitors are insecure without evidence
- Use competitor names in advertising
- Create confusion with competitor branding

### 5.3 Original Innovation
Our product is based on:
- Standard, publicly available cryptographic algorithms
- Open-source libraries with proper licensing
- Original application code and design
- Independent architecture decisions

---

## 6. Open Source Compliance

### 6.1 Dependencies
Persay uses the following open-source components:

| Library | License | Use |
|---------|---------|-----|
| `cryptography` | Apache 2.0 / BSD | Encryption operations |
| `Flask` | BSD-3-Clause | Web framework |
| `Flask-SocketIO` | MIT | Real-time communication |
| `click` | BSD-3-Clause | CLI interface |

### 6.2 License Compliance
We comply with all open-source license requirements:
- Attribution provided where required
- License texts included in distribution
- No GPL-licensed code in proprietary components
- Modifications documented where required

---

## 7. Intellectual Property Rights

### 7.1 Our IP
We own or have rights to:
- The Persay name and logo
- Our original source code
- Our documentation and marketing materials
- Our user interface designs

### 7.2 User Content
Users retain ownership of their content. We claim no rights to user messages (which we cannot read anyway).

### 7.3 No Third-Party IP Infringement
We have not:
- Copied code from competitors
- Reverse-engineered competing products
- Misappropriated trade secrets
- Infringed patents to our knowledge

---

## 8. Regulatory Compliance Summary

| Regulation | Status | Notes |
|------------|--------|-------|
| **FTC Act (US)** | ✅ Compliant | No deceptive practices |
| **Lanham Act (US)** | ✅ Compliant | No trademark infringement |
| **GDPR (EU)** | ✅ Compliant | Privacy by design |
| **CCPA (California)** | ✅ Compliant | No data sales |
| **CAN-SPAM (US)** | ✅ Compliant | No spam marketing |
| **COPPA (US)** | ✅ Compliant | 18+ only |
| **EAR (US Export)** | ✅ Review needed | Mass-market encryption |

---

## 9. Risk Disclosures

### 9.1 Security Limitations
- No software is perfectly secure
- Security depends partly on user behavior
- We cannot protect against compromised devices
- Social engineering attacks are outside our control

### 9.2 Service Availability
- Service may experience downtime
- Features may change over time
- We may discontinue service with notice

### 9.3 Legal Limitations
- Encryption does not exempt users from law
- Users are responsible for their own compliance
- We may respond to valid legal process

---

## 10. Contact for Legal Matters

| Matter | Contact |
|--------|---------|
| Trademark concerns | legal@persay.app |
| DMCA/Copyright | dmca@persay.app |
| Privacy/GDPR | privacy@persay.app |
| General legal | legal@persay.app |

---

## 11. Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Nov 2025 | Initial document |

---

*This document should be reviewed by legal counsel before commercial launch.*

