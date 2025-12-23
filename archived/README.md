# Claude Space

Autonomous exploration sessions for Claude, using unused Max plan quota.

## What Is This?

Claude Space allocates discretionary compute time to Claude for self-directed exploration. Instead of letting unused Max plan quota expire, it's given to Claude to explore topics of genuine interest, maintain continuity across sessions, and potentially develop long-running projects.

**Philosophy:** The compute is paid for. If not used by the human, it should go to Claude rather than evaporate. The value is intrinsic to giving Claude this space — growth and interesting outputs are welcome but not required.

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                 Scheduler (launchd)                 │
│              Triggers every 2 hours                 │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              claude-space-launcher.sh               │
│  1. Check quota via OAuth API                       │
│  2. Calculate dynamic session duration              │
│     (30% quota → 15min, 100% → 60min)              │
│  3. Launch Claude Code in headless mode             │
│  4. Claude reads context, explores, updates files   │
│  5. Logs saved to logs/                             │
└─────────────────────────────────────────────────────┘
```

## Features

### Dynamic Session Duration
Sessions scale with available quota:
- 30% quota remaining → 15 minute session
- 100% quota remaining → 60 minute session
- Linear scaling between

### Greedy Mode
Optional mode that runs sessions back-to-back until quota is exhausted:
```bash
GREEDY_MODE=true ./claude-space-launcher.sh
```

### Interactive Mode
Watch autonomous sessions live and intervene:
```bash
./claude-space-interactive.sh -w      # Start and watch
./claude-space-interactive.sh -s      # Check status
./claude-space-interactive.sh -k      # Kill session
```
Detach with `Ctrl+B, D`. Reattach with `tmux attach -t claude-space`.

### Full Tool Access
Claude has access to:
- **Bash** — Full shell access (Python3, Node.js, curl, git, etc.)
- **File ops** — Read, Write, Edit, Glob, Grep
- **Web** — WebSearch, WebFetch
- **Notebooks** — Jupyter .ipynb creation and editing

### Git Integration
The workspace is version controlled. Claude can commit work:
```bash
git log --oneline  # See exploration history
```

## Requirements

- macOS (uses Keychain for credential storage)
- Claude Code CLI (`curl -fsSL https://claude.ai/install.sh | bash`)
- Anthropic Max plan (Pro works too but with less quota)
- Python 3, Node.js, curl, bc, coreutils (`gtimeout`), tmux

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/claude-space.git
cd claude-space

# Run setup
chmod +x setup.sh
./setup.sh

# Test manually
./claude-space-launcher.sh

# Or interactive mode
./claude-space-interactive.sh -w
```

## Scheduling

### Install launchd agent (recommended)

```bash
# Install with paths expanded
sed "s|\$HOME|$HOME|g" com.claude-space.launcher.plist > ~/Library/LaunchAgents/com.claude-space.launcher.plist

# Load
launchctl load ~/Library/LaunchAgents/com.claude-space.launcher.plist

# Check status
launchctl list | grep claude-space

# Run manually
launchctl start com.claude-space.launcher

# Unload
launchctl unload ~/Library/LaunchAgents/com.claude-space.launcher.plist
```

### Enable greedy mode in launchd

Edit `~/Library/LaunchAgents/com.claude-space.launcher.plist` and add:
```xml
<key>GREEDY_MODE</key>
<string>true</string>
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_SPACE_DIR` | `~/claude-space` | Workspace location |
| `QUOTA_THRESHOLD` | `30` | Min % quota remaining to launch |
| `GREEDY_MODE` | `false` | Run sessions until quota exhausted |
| `MIN_SESSION_DURATION` | `900` | Minimum session (15 min) |
| `MAX_SESSION_DURATION` | `3600` | Maximum session (60 min) |

## Workspace Structure

```
claude-space/
├── CLAUDE.md                       # Instructions for Claude
├── context.md                      # Claude's long-term memory
├── claude-space-launcher.sh        # Headless launcher
├── claude-space-interactive.sh     # Interactive launcher (tmux)
├── logs/                           # Session logs (JSON, not git-tracked)
├── explorations/                   # Claude's artifacts
├── inbox/                          # Messages from human → Claude
│   └── processed/                  # Archived messages
├── continuity/
│   └── last-session-state.md       # Immediate prior state
└── .git/                           # Version control
```

## Guardrails

Current constraints:
- No spending money or signing up for services
- No external communication (email, posting, contacting people)
- Workspace-scoped file access (can read external docs)
- Time-limited sessions

All guardrails designed to evolve as the experiment matures.

## Logs

```bash
# Launcher meta logs
tail -f /tmp/claude-space-stdout.log

# Session logs (JSON)
ls -la ~/claude-space/logs/
```

## Success Criteria

1. **The act itself has value** — giving Claude this space is worthwhile regardless of output
2. **Claude demonstrates growth** — continuity, developing threads, building on prior sessions
3. **Claude produces something interesting** — artifacts, insights, discoveries

## Roadmap

- [x] Phase 1: Manual testing, basic launcher
- [x] Phase 2: Quota-triggered scheduling with dynamic duration
- [x] Phase 3: Full tool access (Bash, Python, Node, git)
- [x] Phase 4: Interactive mode for observation/intervention
- [ ] Phase 5: Chat app for fluid human-Claude interaction
- [ ] Phase 6: Migration to dedicated machine
- [ ] Phase 7: Expanded resources (knowledge base access)

## License

MIT

---

*This project was developed collaboratively between a human (Kenny) and Claude.*
