# LinkedIn Posts

## Formatting Reference for LinkedIn Posts

**Formatting Style:**
- **Section Headers**: Use Unicode bold characters (𝐖𝐡𝐚𝐭, 𝐓𝐡𝐞, etc.) instead of markdown `**bold**`
- **Bullet Points**: Use ▶ (black right-pointing triangle) instead of • or *
- **URLs**: Include zero-width space (​) in URLs to prevent LinkedIn auto-linking
- **Text File**: Generate posts as plain text files (no markdown code blocks) to avoid line numbers when copying

**Unicode Characters Used:**
- Bold text: Mathematical Bold Unicode (𝐀-𝐙, 𝐚-𝐳, 𝟎-𝟗)
- Bullets: ▶ (U+25B6 - Black Right-Pointing Triangle)

**Process:**
1. Write post content in markdown format
2. Convert `**text**` to Unicode bold characters
3. Replace bullet points with ▶
4. Add zero-width spaces to URLs
5. Save as plain text file for clean copy-paste

---

## [November 11, 2024]

New scripts: clean-screenshots​.sh and config/config​.sh

https://github.com/glblackburn/pub-bin/blob/main/README.md#clean-screenshotssh
https://github.com/glblackburn/pub-bin/blob/main/README.md#configconfigsh

I migrated clean-screenshots​.sh from my old private repo and built a new modular configuration system (config/config​.sh) to support it. The script organizes screenshots from your Desktop into timestamped archive directories.

This is one of my daily-use scripts - I take frequent screenshots throughout the day, and this keeps my Desktop clean by automatically organizing them into timestamped archives.

**What clean-screenshots​.sh does:**
* Finds screenshots matching a pattern (default: `Screen*`) in the source directory
* Moves them to timestamped archive directories (e.g., `screenshot_dir/2025-11-11_123456/`)
* Provides detailed output showing what was found and moved
* Supports dry run mode
* Handles configuration interactively if not set up

**What config/config​.sh provides:**
* Generic configuration library for pub-bin scripts
* Interactive setup functions that any script can use
* Config value saving that preserves existing values
* Support for both public and secure config files

**The migration lesson:**
This took way longer than it should have. Cursor decided to rewrite the code from scratch instead of migrating the existing script as-is. I had to provide side-by-side output comparisons from the old and new scripts multiple times to get Cursor to restore functionality that was working fine in the original.

The lesson? When migrating existing code, explicitly tell the AI to migrate first, then refactor. Don't let it "improve" things that already work. Sometimes the best code is the code that's already running in production.

---

## [November 10, 2024](https://www.linkedin.com/posts/activity-7393701785632260097-w13H)

[LinkedIn](https://www.linkedin.com/posts/activity-7393701785632260097-w13H)

New script of the day: monitor-ai-agent-progress​.sh

https://github.com/glblackburn/pub-bin/blob/main/README.md#monitor-ai-agent-progresssh

A monitoring script to track AI agent activity by watching temp files and git changes with audio feedback.

What it does:
* Runs in an infinite loop
* Monitors temp files: counts files in `/tmp/` directory and speaks the count
* Monitors git changes: counts lines in `git diff` and speaks the count with repository name
* Displays the current date
* Configurable update interval (default: 60 seconds)
* Supports quiet and verbose modes

The whole point of this script is to provide audio feedback so you don't have to watch the terminal. It speaks the temp file count and git diff line count (with repository name) so you can track AI agent activity while working on other things.

This is especially useful when working with AI coding assistants on long-running tasks - you can hear when the agent is making changes without constantly checking the terminal.

---

## [November 9, 2024](https://www.linkedin.com/posts/activity-7393305569874407424-DIt6)

[LinkedIn](https://www.linkedin.com/posts/activity-7393305569874407424-DIt6)

I've been developing with AI coding assistants across multiple projects, and I noticed something interesting: each project evolved to have its own set of rules scattered in README files. Some rules were duplicated, some were project-specific, and it was getting hard to maintain consistency.

So I decided to consolidate them. I analyzed AI coding standards across 6 projects and created a standardized reference document (README-AI-CODING-STANDARDS​.md) that all projects now reference.

**The Pattern:**
* Each project has a standardized README-AI-CODING-STANDARDS​.md file with common rules
* Each project's README​.md links to the standardized file
* Project-specific rules stay in each project's README​.md

**What got consolidated:**
* Core Standards (Code Quality, Git Operations, File Creation, Verification)
* General Principles (Readability, Error Handling, DRY, Defensive Programming)
* Bash-Specific Standards (Function Organization, Variable Usage, Error Handling, Code Structure, Best Practices, Script Patterns)
* Common Patterns (Function, Error Handling, Validation)

**The benefits:**
* Consistency across all projects
* Single source of truth for common rules
* Easier to maintain and update
* Projects can still have their own specific rules (like history analysis rules in the bin/history project)

This pattern works really well for maintaining standards across multiple repositories. If you're working with AI coding assistants across multiple projects, consider consolidating your rules into a standardized reference document.

The standardized document is available in the pub-bin repo:

https://github.com/glblackburn/pub-bin/blob/main/README-AI-CODING-STANDARDS​.md

---

## [November 7, 2024](https://www.linkedin.com/posts/activity-7392575729818968065-idu1)

[LinkedIn](https://www.linkedin.com/posts/activity-7392575729818968065-idu1)

So I did a different thing this morning. I have been thinking about how coding agents can help with security. One of the things I wanted to try was doing a full security review using Cursor. Well the post below ticked all the boxes I wanted to try. First, the project looked cool, it gave visibility into something interesting, the project was not too big and it ran with full color in the terminal, which come on just supports the first point.

I forked the GitHub repos and did a security review with Cursor to see what would pop out. Below is a link to the report that Cursor produced with a little coaching.

https://github.com/glblackburn/DEATH_STAR/blob/security-analysis/SECURITY_ANALYSIS.md

I did a screen recording of the process, so stay tuned for that release down the road.

https://www.linkedin.com/posts/pxquirk_cybersecurity-networksecurity-infosec-activity-7391912200308731904-s0vS

---

## [November 6, 2024](https://www.linkedin.com/posts/activity-7392278705642876928-8NDc)

[LinkedIn](https://www.linkedin.com/posts/activity-7392278705642876928-8NDc)

New scripts of the day: fix-spaces-in-filename​.sh and fix-spaces-in-filenames​.sh

https://github.com/glblackburn/pub-bin/blob/main/README.md#fix-spaces-in-filenamesh
https://github.com/glblackburn/pub-bin/blob/main/README.md#fix-spaces-in-filenamessh

Two utility scripts to normalize filenames by removing spaces and special characters.

**fix-spaces-in-filename​.sh** - Renames a single file by replacing non-alphanumeric characters (except dots, slashes, and hyphens) with underscores.

**fix-spaces-in-filenames​.sh** - Batch processes multiple files by calling fix-spaces-in-filename​.sh for each file. Can process from a directory or read file paths from stdin.

What they do:
* fix-spaces-in-filename​.sh: Takes a single file path, validates it exists, replaces non-alphanumeric characters with underscores, and renames the file only if the new name differs
* fix-spaces-in-filenames​.sh: Processes multiple files either from a directory argument or from stdin, finds files with spaces, and calls fix-spaces-in-filename​.sh for each

These scripts are useful for normalizing filenames to remove spaces and special characters, making them more compatible across different systems and easier to work with in scripts.

---

## [November 5, 2024](https://www.linkedin.com/posts/activity-7391806542460846081-IHIq)

[LinkedIn](https://www.linkedin.com/posts/activity-7391806542460846081-IHIq)

New script of the day: load-ssh-key​.sh

https://github.com/glblackburn/pub-bin/blob/main/README.md#load-ssh-keysh

A utility script to automatically load SSH keys from ~/.ssh into the SSH agent.

What it does:
* Finds all SSH private keys in ~/.ssh directory (excludes .pub, known_hosts*, and ssh-agent.config)
* Starts or loads an existing SSH agent configuration
* Checks if each key is already loaded in the agent
* Adds keys to the SSH agent with a timeout (default: 8 hours)
* Verifies keys exist before attempting to load them
* Reports errors if any keys are missing or cannot be loaded

---

## [November 4, 2024](https://www.linkedin.com/posts/activity-7391198472772943873-31zN)

[LinkedIn](https://www.linkedin.com/posts/activity-7391198472772943873-31zN)

So I've started a thing.  For years, I have had what I call a junk drawer of utility scripts.  The git repo contains 135 scripts of which probably about 5 to 10 I used on a daily basis.  The main repo has always been private on GitHub.  Some other repos have only been local to my systems.  I decided a while back that I wanted to start pushing these out for others to see and take away what they can from them.  Over the weekend, I began curating the first of these scripts to migrate to the public GitHub repo.  In my journey to work with AI coding assistance, I am using Cursor to document the repository and manage the README file.  

The repo url is below.  Feel free to take a look, copy what you find useful, and provide feedback if you feel so inclined.

https://github.com/glblackburn/pub-bin
