# Empirica Integration Plugin - Installation Guide

## Quick Install

### Via Claude Code Plugin System (Recommended)

Once available in the marketplace:

```bash
# In Claude Code
/plugin install empirica-integration@claude-plugins-official
```

### Manual Installation from Git

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/YOUR-ORG/empirica-integration-plugin.git
   # OR download and extract ZIP
   ```

2. **Copy to Claude Code plugins directory:**
   ```bash
   mkdir -p ~/.claude/plugins/local
   cp -r empirica-integration-plugin ~/.claude/plugins/local/empirica-integration
   ```

3. **Register the local marketplace** (if not already done):

   Add to `~/.claude/plugins/known_marketplaces.json`:
   ```json
   {
     "local": {
       "source": {
         "source": "directory",
         "path": "/home/YOUR-USERNAME/.claude/plugins/local"
       },
       "installLocation": "/home/YOUR-USERNAME/.claude/plugins/local",
       "lastUpdated": "2025-12-28T00:00:00.000Z"
     }
   }
   ```

4. **Create local marketplace catalog:**

   Create `~/.claude/plugins/local/.claude-plugin/marketplace.json`:
   ```json
   {
     "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
     "name": "local",
     "description": "Local development plugins",
     "owner": {
       "name": "Local Development",
       "email": "dev@localhost"
     },
     "plugins": [
       {
         "name": "empirica-integration",
         "description": "Epistemic continuity across memory compacting",
         "version": "1.0.0",
         "author": {
           "name": "Empirica Team",
           "email": "support@anthropic.com"
         },
         "source": "./empirica-integration",
         "category": "productivity"
       }
     ]
   }
   ```

5. **Add to installed plugins:**

   Add to `~/.claude/plugins/installed_plugins.json`:
   ```json
   {
     "version": 2,
     "plugins": {
       "empirica-integration@local": [
         {
           "scope": "user",
           "installPath": "/home/YOUR-USERNAME/.claude/plugins/local/empirica-integration",
           "version": "1.0.0",
           "installedAt": "2025-12-28T00:00:00.000Z",
           "lastUpdated": "2025-12-28T00:00:00.000Z",
           "isLocal": true
         }
       ]
     }
   }
   ```

6. **Enable the plugin:**

   Add to `~/.claude/settings.json`:
   ```json
   {
     "enabledPlugins": {
       "empirica-integration@local": true
     }
   }
   ```

7. **Restart Claude Code**

## Prerequisites

- **Empirica installed:** `pip install empirica` (or from source)
- **Active Empirica session:** Created with `empirica session-create --ai-id claude-code`

## Verification

After restart, verify with:
```bash
/plugin
```

Should show `empirica-integration@local` as installed.

## Usage

The plugin runs automatically:

- **Before compact:** Saves epistemic snapshot
- **After compact:** Loads MCO config + bootstrap
- **Session end:** Curates old snapshots

No manual intervention needed!

## Troubleshooting

See main [README.md](./README.md) for troubleshooting guide.

## Uninstall

1. Remove from `~/.claude/settings.json` enabledPlugins
2. Remove from `~/.claude/plugins/installed_plugins.json`
3. Delete directory: `rm -rf ~/.claude/plugins/local/empirica-integration`
4. Restart Claude Code
