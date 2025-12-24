---
name: inbox-process
description: Process messages from Kenny in the inbox folder. Use when checking for new messages, reading inbox, handling user requests, or when starting a session to see if Kenny left instructions.
---

# Inbox Process

Handle messages from Kenny that may override normal rotation.

## Steps

1. **Check for messages**
   ```bash
   ls inbox/*.md 2>/dev/null | grep -v '^inbox/processed'
   ```
   If empty, proceed with normal rotation.

2. **Read each message**
   - Messages are markdown files with requests or context from Kenny
   - May contain specific tasks, feedback, or priority overrides

3. **Determine action**
   - If message requests specific work → do that instead of rotation
   - If message is informational → note it, proceed with rotation
   - If message affects multiple sessions → leave in inbox until complete

4. **Archive processed messages**
   ```bash
   mv inbox/message.md inbox/processed/
   ```
   Move only after the request is fully handled.

## Message Priority

Inbox messages take precedence over rotation. If Kenny asks for something specific, do that first.
