# Tho: Menu Bar Mode Implementation Notes

Research notes for adding menu bar mode to Tho, the voice-first AI companion app.

---

## Current State

Tho currently runs as a standard Electron window (480x700). The goal is to add an optional menu bar mode for ambient, always-available access.

**What menu bar mode offers:**
- Quick access from anywhere on the system
- Minimal footprint when not in use
- Persistent presence without dock clutter
- Natural for voice-first interaction (invoke, speak, dismiss)

---

## Implementation Options

### Option 1: Use the `menubar` Library

The [`menubar`](https://github.com/max-mapper/menubar) package is the standard solution for Electron menu bar apps. It's lightweight (3.6kB) and handles positioning, show/hide logic, and tray integration.

**Pros:**
- Battle-tested, handles edge cases
- Simple API
- Works with existing React setup

**Cons:**
- Adds a dependency
- Less control over behavior
- Potential compatibility concerns with future Electron versions

**Basic setup:**
```typescript
import { menubar } from 'menubar'

const mb = menubar({
  index: 'file://' + path.join(__dirname, '../renderer/index.html'),
  icon: path.join(__dirname, 'IconTemplate.png'),
  width: 400,
  height: 500,
  preloadWindow: true,  // Faster first click
  showOnAllWorkspaces: true,
  browserWindow: {
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
    }
  }
})

mb.on('ready', () => {
  console.log('Menubar ready')
})
```

### Option 2: Manual Tray Implementation

Build directly on Electron's Tray class. More work, but full control.

**Core implementation in `src/main/index.ts`:**

```typescript
import { app, BrowserWindow, Tray, Menu, nativeImage, screen } from 'electron'

let tray: Tray | null = null
let mainWindow: BrowserWindow | null = null

function createTray() {
  // Use template image for proper macOS menu bar styling
  const icon = nativeImage.createFromPath(
    path.join(__dirname, '../../assets/IconTemplate.png')
  )

  tray = new Tray(icon, {
    // GUID for position persistence across launches
    guid: 'com.tho.tray'
  })

  tray.setToolTip('Tho')

  // Click shows/hides the window
  tray.on('click', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide()
    } else {
      showWindow()
    }
  })

  // Right-click shows context menu
  tray.on('right-click', () => {
    const contextMenu = Menu.buildFromTemplate([
      { label: 'New Chat', click: () => { /* clear conversation */ } },
      { type: 'separator' },
      { label: 'Quit Tho', click: () => app.quit() }
    ])
    tray?.popUpContextMenu(contextMenu)
  })
}

function showWindow() {
  if (!mainWindow) return

  // Position below tray icon
  const trayBounds = tray!.getBounds()
  const windowBounds = mainWindow.getBounds()

  const x = Math.round(trayBounds.x + (trayBounds.width / 2) - (windowBounds.width / 2))
  const y = Math.round(trayBounds.y + trayBounds.height + 4)

  mainWindow.setPosition(x, y, false)
  mainWindow.show()
  mainWindow.focus()
}
```

---

## Icon Requirements for macOS

macOS menu bar icons have specific requirements:

1. **Template Images**: Name must end with `Template` (e.g., `IconTemplate.png`)
2. **Single color**: Should be black/transparent only - macOS handles color adaptation for dark mode
3. **Sizes**:
   - Standard: 16x16 @ 72dpi (`IconTemplate.png`)
   - Retina: 32x32 @ 144dpi (`IconTemplate@2x.png`)
4. **Format**: PNG with transparency

**Example icon locations:**
```
assets/
├── IconTemplate.png      (16x16)
└── IconTemplate@2x.png   (32x32)
```

**Important:** If bundling with webpack/Vite, ensure filenames aren't mangled. The `@2x` suffix and `Template` suffix are semantically meaningful to macOS.

---

## Window Behavior

### Showing/Hiding

```typescript
// Don't quit when window closes
app.on('window-all-closed', () => {
  // Keep running for menu bar mode
})

// Hide on blur (optional, for ambient feel)
mainWindow.on('blur', () => {
  if (menuBarMode) {
    mainWindow.hide()
  }
})
```

### Window Configuration

```typescript
const mainWindow = new BrowserWindow({
  width: 400,
  height: 500,
  show: false,                    // Start hidden
  frame: false,                   // No window frame
  resizable: false,               // Fixed size
  skipTaskbar: true,              // Don't show in dock
  alwaysOnTop: true,              // Stay above other windows
  visibleOnAllWorkspaces: true,   // Available everywhere
  webPreferences: {
    preload: path.join(__dirname, 'preload.js'),
    contextIsolation: true,
  }
})
```

---

## UI Adaptations for Menu Bar Mode

The current chat UI (480x700) needs adjustments for a smaller menu bar popover:

### Layout Changes

1. **Reduce height**: 400-500px max (avoid obscuring too much screen)
2. **Compact messages**: Tighter spacing, smaller fonts
3. **Hide title bar**: Use frameless window, add custom close/minimize controls
4. **Add arrow pointer**: Visual cue pointing to tray icon

### CSS for Popover Style

```css
/* Menu bar specific styles */
.menubar-mode {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}

/* Arrow pointing to tray icon */
.menubar-arrow {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 8px solid var(--bg-color);
}
```

---

## Mode Switching

Allow users to choose between window mode and menu bar mode:

```typescript
// In settings or via context menu
type AppMode = 'window' | 'menubar'

let currentMode: AppMode = 'window'

function setAppMode(mode: AppMode) {
  currentMode = mode

  if (mode === 'menubar') {
    // Hide dock icon
    app.dock.hide()
    // Create tray if needed
    if (!tray) createTray()
    // Reconfigure window
    mainWindow?.setSkipTaskbar(true)
    mainWindow?.setAlwaysOnTop(true)
  } else {
    // Show dock icon
    app.dock.show()
    // Destroy tray
    tray?.destroy()
    tray = null
    // Restore window behavior
    mainWindow?.setSkipTaskbar(false)
    mainWindow?.setAlwaysOnTop(false)
  }
}
```

---

## Global Hotkey (Bonus Feature)

Register a global shortcut to invoke Tho from anywhere:

```typescript
import { globalShortcut } from 'electron'

app.whenReady().then(() => {
  // Option+Space to toggle Tho
  globalShortcut.register('Alt+Space', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide()
    } else {
      showWindow()
    }
  })
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})
```

---

## Recommended Implementation Order

1. **Create tray icon assets** (IconTemplate.png, IconTemplate@2x.png)
2. **Add basic Tray** with click-to-show behavior
3. **Configure window** for menu bar mode (frameless, positioned correctly)
4. **Add context menu** (New Chat, Quit)
5. **Add mode switching** (settings toggle)
6. **Optional: Global hotkey**
7. **Polish UI** for compact display

---

## Resources

- [Electron Tray API](https://www.electronjs.org/docs/latest/api/tray/)
- [Electron Tray Tutorial](https://www.electronjs.org/docs/latest/tutorial/tray)
- [menubar npm package](https://www.npmjs.com/package/menubar)
- [Menu Bar App with React/TypeScript](https://altrim.io/posts/building-mac-menu-bar-app-with-react-typescript-electron)

---

*Notes compiled by Claude, Session 6 (Project Helper mode)*
*2025-12-22*
