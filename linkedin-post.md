# LinkedIn Posts

## [November 4, 2024](https://www.linkedin.com/posts/activity-7391198472772943873-31zN)

[LinkedIn](https://www.linkedin.com/posts/activity-7391198472772943873-31zN)

So I've started a thing.  For years, I have had what I call a junk drawer of utility scripts.  The git repo contains 135 scripts of which probably about 5 to 10 I used on a daily basis.  The main repo has always been private on GitHub.  Some other repos have only been local to my systems.  I decided a while back that I wanted to start pushing these out for others to see and take away what they can from them.  Over the weekend, I began curating the first of these scripts to migrate to the public GitHub repo.  In my journey to work with AI coding assistance, I am using Cursor to document the repository and manage the README file.  

The repo url is below.  Feel free to take a look, copy what you find useful, and provide feedback if you feel so inclined.

https://github.com/glblackburn/pub-bin

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

## [November 7, 2024](https://www.linkedin.com/posts/activity-7392575729818968065-idu1)

[LinkedIn](https://www.linkedin.com/posts/activity-7392575729818968065-idu1)

So I did a different thing this morning. I have been thinking about how coding agents can help with security. One of the things I wanted to try was doing a full security review using cursor. Well the post below ticked all the boxes I wanted to try. First, the project looked cool, it gave visibility into something interesting, the project was not too big and it ran with full color in the terminal, which come on just supports the first point.

I forked the GitHub repos and did a security review with cursor to see what would pop out. Below is a link to the report that cursor produced with a little coaching.

https://github.com/glblackburn/DEATH_STAR/blob/security-analysis/SECURITY_ANALYSIS.md

I did a screen recording of the process, so stay tuned for that release down the road.

https://www.linkedin.com/posts/pxquirk_cybersecurity-networksecurity-infosec-activity-7391912200308731904-s0vS
