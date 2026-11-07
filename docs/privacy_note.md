# Privacy Note & Data Protection Disclosure

## 1. Zero Personal Data Collection (Zero PII)
- **No User Account Required**: Voters use this service anonymously without sign-up, email, phone number, or voter card numbers (VIN).
- **Ephemeral Session Processing**: User queries are processed strictly in-memory during request execution and are never saved to disk, databases, or analytics engines.
- **No Cookie Tracking**: The web interface does not set tracking cookies, local storage identifiers, or fingerprint devices.

## 2. Privacy-Preserving Link Checking (Google Safe Browsing Update API v4)
- When a user submits a URL to verify whether it is a known malicious or phishing site:
  1. The user's full URL is **never** transmitted to Google, INEC, or any third party.
  2. The system maintains a local encrypted database of 4-byte SHA-256 hash prefixes fetched periodically via Google's `threatListUpdates:fetch` endpoint.
  3. The URL is canonicalized and hashed locally on the server.
  4. Only in the rare event of a 4-byte hash collision does the server send the truncated 4-byte prefix to `fullHashes:find` to retrieve potential matches for local comparison.
  5. Because millions of unrelated URLs share the same 4-byte prefix, no external party can discern what URL the voter checked.

## 3. Transparency & Disclosures
Every user check interface displays:
> *"Privacy Notice: Your queries and links are never stored or shared. URL safety checks use zero-knowledge local cryptographic hashing."*
