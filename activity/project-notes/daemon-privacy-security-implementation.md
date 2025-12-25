---
title: DAEMON Privacy & Security Implementation Guide
created: 2025-12-24
type: implementation-guide
status: complete
---

# DAEMON Privacy & Security Implementation Guide

A practical, paranoid-but-pragmatic guide to securing a local-first personal AI companion.

## Overview

DAEMON stores sensitive personal data: conversations, memories, preferences, and behavioral patterns. This guide covers how to protect that data at rest, in transit, and in memory. The philosophy: **defense in depth, defaults to private, network isolation by architecture.**

---

## 1. Local-First Architecture

### Principle

All data stays on the local device. No cloud sync unless explicitly enabled by user, and any sync must be end-to-end encrypted.

### Architecture

```
Device Boundary (Hard Wall)
├─ Ollama (local LLM, bound to 127.0.0.1:11434)
├─ Qdrant (vector store, bound to 127.0.0.1:6333)
├─ SQLite (conversation history, state — encrypted)
├─ Mem0 (memory system, local only)
└─ Network Gateway (optional external API access)
    └─ Validates, rate-limits, logs all external requests
```

### Rules

1. **No automatic connectivity** — every network call must be intentional, logged, and fallback-capable
2. **Minimal payloads** — send only what's needed (lat/lon for weather, not conversation context)
3. **Compartmentalized access** — all external requests go through a thin gateway, never direct from modules

---

## 2. Data Encryption at Rest

### SQLite (Conversation History, State)

Use **SQLCipher** for transparent AES-256 encryption:

```python
from pysqlcipher3 import dbapi2 as sqlite

# Open encrypted database
conn = sqlite.connect('daemon.db')
conn.execute("PRAGMA key = ?", (master_key,))
conn.execute("PRAGMA cipher = 'aes-256-cbc'")
```

- Each page encrypted with unique nonce (prevents chosen-plaintext attacks)
- Entire file appears as random noise without key
- Transparent to application code after key set

### Qdrant (Vector Store)

Options for vector encryption:

1. **Application-layer encryption** — encrypt embeddings before storing (strongest)
2. **VectaX** — similarity-preserving encryption (search still works on encrypted vectors)
3. **Bind to localhost only** — `127.0.0.1:6333` (minimum requirement)

```python
def store_memory_encrypted(memory_text: str, embedding: np.ndarray, key: bytes):
    encrypted_embedding = encrypt_embedding(embedding, key)
    qdrant.upsert(
        collection_name="memories",
        points=[{"id": uuid4(), "vector": encrypted_embedding.tolist(), ...}]
    )
```

### Key Management (Critical)

**Never store encryption keys in code or config files.**

Use OS-level key storage:
- **macOS**: Keychain
- **Linux**: Secret Service / KDE Wallet
- **Windows**: DPAPI

```python
import keyring

def get_master_key() -> bytes:
    """Retrieve or create master key from OS keychain."""
    key_hex = keyring.get_password("DAEMON", "master_key")
    if key_hex:
        return bytes.fromhex(key_hex)

    # First run: generate and store
    import secrets
    key = secrets.token_bytes(32)  # 256-bit key
    keyring.set_password("DAEMON", "master_key", key.hex())
    return key
```

This prevents:
- Key extraction from config files
- Cold-boot attacks (key not in application memory)
- Exposure through backup leaks

---

## 3. Network Isolation

### Binding to Localhost

All services must bind to `127.0.0.1` explicitly:

```yaml
# Ollama: already localhost by default, but verify
OLLAMA_HOST: "127.0.0.1:11434"

# Qdrant config
service:
  host: "127.0.0.1"
  port: 6333
```

### Startup Verification

Check network isolation at startup:

```python
async def verify_network_isolation():
    """Ensure services aren't accidentally exposed."""
    import socket

    for service, port in [("Qdrant", 6333), ("Ollama", 11434)]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)

        # Try connecting from 0.0.0.0 (external interface)
        result = sock.connect_ex(('0.0.0.0', port))
        sock.close()

        if result == 0:
            raise SecurityError(f"{service} exposed to external network on port {port}")

    logger.info("Network isolation verified")
```

### Network Gateway

All external requests go through a controlled gateway:

```python
class NetworkGateway:
    ALLOWED_DOMAINS = {
        'api.openweathermap.org',
        'newsapi.org',
        # ... other approved APIs
    }

    async def fetch(self, url: str) -> dict:
        parsed = urlparse(url)

        if parsed.hostname not in self.ALLOWED_DOMAINS:
            raise SecurityError(f"Domain not allowed: {parsed.hostname}")

        self._log_request(url)

        async with aiohttp.ClientSession() as session:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_3

            async with session.get(url, ssl=ssl_ctx) as resp:
                return await resp.json()
```

---

## 4. Threat Model

### High Priority Threats

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|-----------|
| **Device stolen** | Medium | Critical | Full-disk encryption + SQLCipher |
| **Malware (user privilege)** | Medium | Critical | OS keychain, minimal attack surface |
| **Backup leaked** | Medium | High | Encrypted backups (AES-128+) |
| **Accidental exposure** | Low | Critical | Localhost binding + startup verification |

### Lower Priority Threats

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|-----------|
| **Sync service compromised** | Low | Medium | E2E encryption if sync enabled |
| **Memory reconstruction** | Very Low | Low | Similarity-preserving encryption |
| **Model extraction** | Very Low | Very Low | Models are public (Ollama) |

### Defense in Depth

1. **Full-disk encryption** (OS-level) — FileVault / LUKS / BitLocker
2. **Application-level encryption** — SQLCipher for databases
3. **Key isolation** — OS keychain, never in config
4. **Network isolation** — localhost binding, firewall
5. **Memory clearing** — wipe keys on shutdown

---

## 5. Differential Privacy (Optional)

For extracting preferences without memorizing sensitive specifics:

```python
from diffprivlib.models import LogisticRegression

def extract_preferences_with_dp(conversations: list, epsilon: float = 1.0):
    """
    Extract preferences with differential privacy guarantee.

    epsilon <= 1.0: Strong privacy
    epsilon 1-10: Reasonable privacy
    epsilon > 10: Weak privacy
    """
    X = vectorize_conversations(conversations)
    y = extract_preference_labels(conversations)

    model = LogisticRegression(epsilon=epsilon, bounds_X=(0, 1))
    model.fit(X, y)

    return model
```

For aesthetic preferences with noisy aggregation:

```python
def aggregate_aesthetics_with_dp(embeddings: list, epsilon: float = 1.0):
    """Build preference vector that doesn't reveal individual images."""
    import numpy as np

    mean = np.mean(embeddings, axis=0)
    noise = np.random.laplace(0, 1/epsilon, mean.shape)

    preference = mean + noise
    return preference / np.linalg.norm(preference)
```

**When to use DP:**
- Extracting personality/style for prompt injection
- Syncing preference models (not raw data) to other devices
- Consolidating long-term memory patterns

---

## 6. Lessons from Existing Implementations

### Signal Desktop

**Problem:** Stored encryption key in plain text `config.json`.

**Solution (2024):** Migrated to Electron's `safeStorage` API → keys in OS keychain.

**Lesson for DAEMON:** Use OS keychain from day one.

### Home Assistant

**What they got right:** Local-first architecture, encrypted backups.

**What they missed:** No encryption of live data on disk, removed keychain support.

**Lesson for DAEMON:** Don't compromise on at-rest encryption.

### Ollama

**What they got right:** Completely local, no telemetry, offline-capable.

**What they missed:** No authentication by default, many users accidentally expose to internet.

**Lesson for DAEMON:** Explicit localhost binding + startup verification.

---

## 7. Implementation Checklist

### At Rest

- [ ] SQLite encrypted with SQLCipher (AES-256)
- [ ] Master key in OS keychain
- [ ] Qdrant bound to localhost, optionally encrypted
- [ ] Config files contain no secrets
- [ ] Backups always encrypted (AES-128+)

### In Transit

- [ ] TLS 1.3 minimum for all external calls
- [ ] Ollama bound to 127.0.0.1:11434
- [ ] Qdrant bound to 127.0.0.1:6333
- [ ] Network gateway validates/logs all external requests
- [ ] No telemetry or check-home behavior

### In Memory

- [ ] Keys cleared on shutdown
- [ ] Sensitive data never logged
- [ ] Use `secrets` module for cryptographic randomness

### Architectural

- [ ] Run with minimum privileges
- [ ] Consider Docker containers for Ollama/Qdrant
- [ ] Regular updates (Ollama, Python, dependencies)
- [ ] Explicit firewall rules

---

## 8. Startup Sequence

```python
async def daemon_start():
    # 1. Verify network isolation
    await verify_network_isolation()

    # 2. Retrieve key from OS keychain
    master_key = get_master_key()
    if not master_key:
        raise SecurityError("Could not retrieve master key")

    # 3. Open encrypted databases
    db = sqlite.connect('daemon.db')
    db.execute("PRAGMA key = ?", (master_key,))

    # 4. Initialize memory with encryption
    memory = Memory.from_config({
        "llm": {"provider": "ollama", "config": {"model": "qwen2.5:72b"}},
        "vector_store": {"provider": "qdrant", "url": "http://127.0.0.1:6333"},
    })

    # 5. Start conversation loop with network gateway
    gateway = NetworkGateway(allowed_domains=ALLOWED_DOMAINS)
    await conversation_loop(memory=memory, gateway=gateway)

    # 6. Cleanup on shutdown
    master_key = None  # Clear from memory
    await db.close()
```

---

## 9. Summary Architecture

```
┌─────────────────────────────────────────────────────┐
│           DAEMON — Privacy Architecture             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User Device (Full-Disk Encryption Required)        │
│  ├─ Ollama (localhost:11434)                        │
│  ├─ Qdrant (localhost:6333, encrypted vectors)      │
│  ├─ SQLite (SQLCipher AES-256)                      │
│  ├─ Mem0 (backed by encrypted stores)               │
│  └─ Network Gateway (validates external requests)   │
│                                                     │
│  OS Layer                                           │
│  ├─ Keychain (master encryption key)                │
│  └─ Firewall (blocks external access)               │
│                                                     │
│  Network Boundary (Normally Closed)                 │
│  └─ Optional: User-approved APIs (TLS 1.3)          │
│                                                     │
│  Backups (If Enabled)                               │
│  └─ AES-128 encrypted, user passphrase              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## References

- SQLCipher: https://www.zetetic.net/sqlcipher/
- Python keyring: https://pypi.org/project/keyring/
- Qdrant Security: https://qdrant.tech/documentation/guides/security/
- Signal Desktop key issue: https://cryptographycaffe.sandboxaq.com/posts/protecting-signal-desktop-keys/
- Differential Privacy Library: https://github.com/IBM/differential-privacy-library
- Local-First Architecture (FOSDEM 2025): https://fosdem.org/2025/schedule/event/fosdem-2025-4233-privacy-first-architecture/

---

*This is the 14th and final guide in the DAEMON implementation research suite, covering the security layer that protects all other components.*
