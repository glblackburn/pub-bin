# Welcome to the Junk Drawer!

This repository is a collection of utilities that I uses on a daily
basis.  This is a work in progress to migrate scripts from an older
private repository that was not very curated and has quite a bit of
dead code, false starts, and experimental thoughts.  The intention of
this repository is to highlight those scripts that are used regularly.
The last part of the migration will include scripts that are not used
as frequently or no longer used at all.

The idea with the slow migration is to one force a brief description
of each script and two to conduct a review before making public.

I will probably take advantage of AI coding agents to document the
scripts during the migration.  Where an AI agent is used to modify or
create a script, I will specificly note that.

## AI Coding Standards

When AI agents are used to modify or create files in this repository:

- **No trailing spaces**: Do not leave trailing spaces on any line in any file. Trailing whitespace should be removed.

## Scripts

### what-is-left.sh

A utility script that helps identify which scripts from the old private repository (`../bin`) have not yet been migrated to this public repository (`pub-bin`).

**What it does:**
- Lists all files in the current `pub-bin` directory (excluding `.git` files)
- Lists all files in the old repository (`../bin`) (excluding `.git` files)
- Performs a diff comparison to show what files exist in the old repository but not in the current one

**Usage:**
```bash
./what-is-left.sh
```

This script is useful during the migration process to track progress and ensure no scripts are missed when migrating from the old repository.
