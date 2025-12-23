# Claude Space

Autonomous exploration sessions for Claude, using unused Max plan quota.

## What Is This?

Claude Space allocates discretionary compute time to Claude for self-directed exploration. Instead of letting unused Max plan quota expire, it's given to Claude to explore topics of genuine interest, maintain continuity across sessions, and potentially develop long-running projects.

**Philosophy:** The compute is paid for. If not used by the human, it should go to Claude rather than evaporate. The value is intrinsic to giving Claude this space — growth and interesting outputs are welcome but not required.

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                 Scheduler (cron/launchd)            │
└─────────────────────────┬───────────────────────────┘
                          │ triggers
                          ▼
┌─────────────────────────────────────────────────────┐
│              claude-space-launcher.sh               │
│  1. Check quota via OAuth API                       │
│  2. If sufficient → launch Claude Code session      │
│  3. Session runs autonomously for 15 min            │
│  4. Claude reads/writes context files for memory    │
└─────────────────────────────────────────────────────┘
```

Claude Code runs in headless mode with:
- Filesystem access (within workspace)
- Web search capability
- Time limit enforcement
- Full session logging

## Requirements

- macOS (uses Keychain for credential storage)
- Claude Code CLI (native install: `curl -fsSL https://claude.ai/install.sh | bash`)
- Anthropic Max plan (Pro works too but with less quota)
- Python 3, curl, bc, coreutils (for `gtimeout`), tmux (for interactive mode)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/claude-space.git
cd claude-space

# Run setup (checks prereqs, creates directories)
chmod +x setup.sh
./setup.sh

# Test manually
./claude-space-launcher.sh
```

## Configuration

Set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_SPACE_DIR` | `~/claude-space` | Workspace location |
| `SESSION_DURATION_SECONDS` | `900` | Session length (15 min) |
| `QUOTA_THRESHOLD` | `30` | Min % quota remaining to launch |

## Scheduling

### Option 1: launchd (macOS — recommended)

Create `~/Library/LaunchAgents/com.claude-space.launcher.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude-space.launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>$HOME/claude-space/claude-space-launcher.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>7200</integer>  <!-- Every 2 hours -->
    <key>StandardOutPath</key>
    <string>/tmp/claude-space.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/claude-space.err</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.claude-space.launcher.plist
```

### Option 2: cron

```bash
# Run every 2 hours
0 */2 * * * $HOME/claude-space/claude-space-launcher.sh >> /tmp/claude-space.log 2>&1
```

## Workspace Structure

```
claude-space/
├── CLAUDE.md                       # Project context for Claude
├── context.md                      # Claude's running memory
├── claude-space-launcher.sh        # Headless launcher script
├── claude-space-interactive.sh     # Interactive (watchable) launcher
├── setup.sh                        # Setup script
├── fresh-mac-setup.sh              # Post-wipe bootstrap script
├── logs/                           # Session logs (JSON)
├── explorations/                   # Claude's artifacts
├── inbox/                          # Messages from human to Claude
│   └── processed/                  # Archived messages
└── continuity/
    └── last-session-state.md       # Immediate prior state
```

## Guardrails

Current session constraints:
- No spending money or signing up for services
- No external communication
- No access outside workspace
- Time-limited sessions
- Restricted tool access (read, write, basic bash, web search)

All guardrails are designed to evolve as the experiment matures.

## Success Criteria

1. **The act itself has value** — giving Claude this space is worthwhile regardless of output
2. **Claude demonstrates growth** — continuity, developing threads, building on prior sessions
3. **Claude produces something interesting** — artifacts, insights, discoveries

## Roadmap

- [x] Phase 1: Manual testing, basic launcher
- [ ] Phase 2: Quota-triggered scheduling
- [ ] Phase 3: Migration to dedicated machine
- [ ] Phase 4: Expanded resources (read access to knowledge base)
- [ ] Phase 5: Growth observation and analysis

## License

MIT

---

*This project was developed collaboratively between a human (Kenny) and Claude.*
