---
name: apple-ecosystem
description: Integrate with macOS Apple services from Hermes — Notes, Reminders, FindMy, iMessage, and macOS Computer Use automation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Apple, macOS, Notes, Reminders, FindMy, iMessage, Computer-Use, Automation]
    related_skills: []
---

# Apple Ecosystem Integration

This umbrella skill covers five macOS-only Apple service tools. All require macOS with the relevant Apple app installed and signed in to iCloud.

## Sections

### 1. Apple Notes (`apple-notes`)

Manage Apple Notes via `memo` CLI. Create, search, edit notes. Syncs across Apple devices via iCloud.

**Prerequisites:**
- macOS with Notes.app
- `brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app (System Settings → Privacy → Automation)

**Quick Reference:**
```bash
memo list                                  # List all notes (YAML)
memo list | grep -c "^  "                  # Count notes
memo list | head -20                       # Recent notes
memo search "keyword"                      # Search note titles
memo search "keyword" | head -3            # Top 3 matches
memo add "Note title" "Note content"       # Create a note
memo add "Title" "Body..." --folder "Folder"  # Create in specific folder
memo open "Note title first few words..."  # Open note in Notes.app
memo export "Note title"                   # Export to stdout (Markdown)
memo export "Note title" --dest ./out.md   # Export to file
memo delete "Note title"                   # Delete a note
```

### 2. Apple Reminders (`apple-reminders`)

Manage Apple Reminders via `remindctl` CLI. Create and manage to-dos that sync to iOS.

**Prerequisites:**
- macOS with Reminders.app
- `brew install steipete/tap/remindctl`
- Grant Reminders permission when prompted

**Quick Reference:**
```bash
remindctl list                    # List all reminders
remindctl add "Buy milk"          # Add a reminder
remindctl add "Meeting at 3" --due "2026-06-07 15:00"  # With due date
remindctl add "Task" --list "Work"  # To specific list
remindctl done <id>               # Complete a reminder
remindctl status                  # Check authorization status
remindctl authorize               # Request authorization
```

### 3. FindMy (`findmy`)

Track Apple devices and AirTags via FindMy.app using AppleScript + screenshot capture.

**Prerequisites:**
- macOS with Find My app, iCloud signed in
- Screen Recording permission for terminal (System Settings → Privacy → Screen Recording)
- Optional: `brew install steipete/tap/peekaboo` for better UI automation

**Method 1 — AppleScript + Screenshot (Basic):**
```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'
# Wait, then capture screenshot of device locations
```

**Method 2 — peekaboo (Advanced):**
```bash
peekaboo --findmy                             # Refresh and list all items
peekaboo --findmy --json                      # JSON output for parsing
peekaboo --findmy --items-only                # Just item names and locations
peekaboo --findmy --watch 'Item Name' --interval 5  # Track movement
```

### 4. iMessage (`imessage`)

Send and read iMessages/SMS via `imsg` CLI through macOS Messages.app.

**Prerequisites:**
- macOS with Messages.app signed in
- `brew install steipete/tap/imsg`
- Grant Full Disk Access (System Settings → Privacy → Full Disk Access)
- Grant Automation permission for Messages.app

**Quick Reference:**
```bash
imsg send "+15551234567" "Hello!"       # Send to phone number
imsg send "user@icloud.com" "Hi"        # Send to email/Apple ID
imsg send "John" "Message"              # Send to contact name
imsg conversations                       # List recent conversations
imsg conversations -n 5                  # Last 5 conversations
imsg read --last                         # Read latest unread message
imsg read --thread "John" -n 10         # Read last 10 from a thread
```

### 5. macOS Computer Use (`macos-computer-use`)

Drive the macOS desktop in background via `computer_use` tool — screenshots, mouse, keyboard, scroll, drag. Does not steal user's cursor or Space.

**Usage:**
```text
Available via the computer_use tool. Canonical workflow:
1. computer_use(action="capture", mode="som", app="Safari")
2. computer_use(action="click", ref="...")
3. computer_use(action="type", text="...")
```

**Key actions:** `capture`, `click`, `type`, `scroll`, `drag`, `key`, `open`, `launch`.
**Modes:** `som` (numbered overlays), `ax` (accessibility tree), `raw` (full screenshot).

---

## Pitfalls

- All tools are **macOS-only** and will error on Linux/Windows
- Most require granting system permissions (Automation, Screen Recording, Full Disk Access, Accessibility)
- `imsg` and `memo` are brew-installed third-party CLIs — may lag behind macOS updates
- `findmy` via AppleScript is fragile; `peekaboo` is preferred when installed
- For FindMy, device locations update asynchronously — location shown may be stale
- iMessage sending requires the Messages app to be signed in and running