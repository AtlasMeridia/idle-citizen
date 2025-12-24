# App Support

Internal files for Idle Citizen operation. Not part of the activity system.

**Note:** The launcher is macOS-only. It uses launchd, Keychain, AppleScript, and other macOS-specific APIs. Linux support would require a separate launcher script with systemd/cron, different credential storage, and alternative terminal handling.

## Directory Contents

```
app support/
├── archived/       # Old files, kept for reference
├── continuity/     # Session state tracking
│   ├── last-session-state.md
│   └── activity-rotation.txt
├── dev/            # Development/experimental files
├── logs/           # Auto-generated session logs
└── scripts/        # Launcher scripts
```

## Setup on a New Machine

Idle Citizen requires a **launchd plist** to run automatically. This file lives outside the repo at `~/Library/LaunchAgents/` and must be created manually.

### 1. Create the plist

```bash
cat > ~/Library/LaunchAgents/com.idle-citizen.launcher.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.idle-citizen.launcher</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-l</string>
        <string>-c</string>
        <!-- UPDATE THIS PATH to your idle-citizen location -->
        <string>/Users/YOUR_USERNAME/Projects/idle-citizen/app support/scripts/idle-citizen-launcher.sh</string>
    </array>

    <!-- Run every 1 hour (3600 seconds) -->
    <key>StartInterval</key>
    <integer>3600</integer>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>/tmp/idle-citizen-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/idle-citizen-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <!-- UPDATE THIS PATH to include your local bin locations -->
        <string>/Users/YOUR_USERNAME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>IDLE_CITIZEN_DIR</key>
        <!-- UPDATE THIS PATH to your idle-citizen location -->
        <string>/Users/YOUR_USERNAME/Projects/idle-citizen</string>
        <key>QUOTA_THRESHOLD</key>
        <string>30</string>
    </dict>

    <key>KeepAlive</key>
    <false/>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
EOF
```

### 2. Update the paths

Replace `YOUR_USERNAME` with your actual username, or adjust paths if idle-citizen is in a different location:

```bash
sed -i '' "s|YOUR_USERNAME|$(whoami)|g" ~/Library/LaunchAgents/com.idle-citizen.launcher.plist
```

### 3. Load the agent

```bash
launchctl load ~/Library/LaunchAgents/com.idle-citizen.launcher.plist
```

### 4. Verify it's running

```bash
launchctl list | grep idle-citizen
```

## Managing the Launcher

**Start manually (test):**
```bash
launchctl start com.idle-citizen.launcher
```

**Stop/unload:**
```bash
launchctl unload ~/Library/LaunchAgents/com.idle-citizen.launcher.plist
```

**View logs:**
```bash
tail -f /tmp/idle-citizen-stdout.log
tail -f /tmp/idle-citizen-stderr.log
```

**Check session logs:**
```bash
ls -la "app support/logs/"
```

## Prerequisites

Before the launcher will work:

1. **Claude Code CLI** must be installed and authenticated
   ```bash
   claude --version
   ```

2. **GNU coreutils** for `gtimeout` (macOS)
   ```bash
   brew install coreutils
   ```

3. **jq** for log parsing in watch mode
   ```bash
   brew install jq
   ```

## Configuration

Environment variables (set in plist or export before running):

| Variable | Default | Description |
|----------|---------|-------------|
| `IDLE_CITIZEN_DIR` | `~/idle-citizen` | Workspace path |
| `QUOTA_THRESHOLD` | `30` | Min % quota to start session |
| `GREEDY_MODE` | `false` | Loop sessions until quota exhausted |
| `WATCH_SESSION` | `true` | Open Terminal window to watch |
