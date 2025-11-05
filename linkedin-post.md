# LinkedIn Posts

## [November 4, 2024](https://www.linkedin.com/posts/activity-7391198472772943873-31zN)

[LinkedIn](https://www.linkedin.com/posts/activity-7391198472772943873-31zN)

So I've started a thing.  For years, I have had what I call a junk drawer of utility scripts.  The git repo contains 135 scripts of which probably about 5 to 10 I used on a daily basis.  The main repo has always been private on GitHub.  Some other repos have only been local to my systems.  I decided a while back that I wanted to start pushing these out for others to see and take away what they can from them.  Over the weekend, I began curating the first of these scripts to migrate to the public GitHub repo.  In my journey to work with AI coding assistance, I am using Cursor to document the repository and manage the README file.  

The repo url is below.  Feel free to take a look, copy what you find useful, and provide feedback if you feel so inclined.

https://github.com/glblackburn/pub-bin

---

## [November 5, 2024](https://www.linkedin.com/posts/activity-7391806542460846081-IHIq)

[LinkedIn](https://www.linkedin.com/posts/activity-7391806542460846081-IHIq)

New script of the day: load-ssh-key.sh

https://github.com/glblackburn/pub-bin/blob/main/README.md#load-ssh-keysh

A utility script to automatically load SSH keys from ~/.ssh into the SSH agent.

What it does:
* Finds all SSH private keys in ~/.ssh directory (excludes .pub, known_hosts*, and ssh-agent.config)
* Starts or loads an existing SSH agent configuration
* Checks if each key is already loaded in the agent
* Adds keys to the SSH agent with a timeout (default: 8 hours)
* Verifies keys exist before attempting to load them
* Reports errors if any keys are missing or cannot be loaded
