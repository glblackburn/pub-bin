## [December 9, 2025](https://www.linkedin.com/posts/activity-7404914508818927617-7PK8)

[LinkedIn](https://www.linkedin.com/posts/activity-7404914508818927617-7PK8)

---

monitor-ai-agent-progress.sh: Major updates with new features  

Just finished a series of updates to monitor-ai-agent-progress.sh. The script has evolved from a simple temp file and git diff monitor into a comprehensive AI agent activity tracker.  

𝐖𝐡𝐚𝐭'𝐬 𝐧𝐞𝐰:  
▶ File-based git status counting: Replaced line counting with proper file counting (handles untracked directories recursively)  
▶ Process monitoring: New -p flag to monitor system process count  
▶ Work metric refactoring: Hidden by default (use -w to show), -W flag for path display  
▶ Repository/branch display: New -r flag shows repo and branch as separate line  
▶ Audio changes-only mode: New -c flag to only announce when metrics change (reduces noise)  
▶ Better formatting: Column-aligned output with centered status indicators  

𝐖𝐡𝐲 𝐭𝐡𝐞𝐬𝐞 𝐜𝐡𝐚𝐧𝐠𝐞𝐬 𝐦𝐚𝐭𝐭𝐞𝐫:  
When monitoring AI agent activity, you want to understand the scope of work. The old line-counting approach would show "1" for an untracked directory with dozens of files. File-based counting shows the actual number of files being created or modified.  

The audio changes-only mode (-c flag) is a game-changer. Instead of constant announcements every 60 seconds, you only hear updates when something actually changes. Much less distracting when working on other tasks.  

𝐓𝐡𝐞 𝐥𝐞𝐬𝐬𝐨𝐧:  
This script has been a great example of iterative improvement. Started simple, then added features as I discovered what I actually needed. The opt-in approach for metrics keeps default output clean while providing powerful monitoring when needed. Sometimes less is more, especially for tools you run continuously.  

monitor-ai-agent-progress.sh: Comprehensive AI agent activity monitoring with audio feedback  
https://github.com/glblackburn/pub-bin/blob/main/monitor-ai-agent-progress.sh
