## Table of Contents

- [Set different ssh keys for multiple GitHub users](#set-different-ssh-keys-for-multiple-github-users)
- [SSH Key Usage Pitfalls](#ssh-key-usage-pitfalls)
- [Apache Infrastructure Downtime Report](#apache-infrastructure-downtime-report)
- [Markdown Viewer Chrome Extension](#markdown-viewer-chrome-extension)

# Set different ssh keys for multiple GitHub users
* https://stackoverflow.com/questions/29023532/how-do-i-use-multiple-ssh-keys-on-github

Configure the users in ~/.ssh/config
```
Host glblackburn
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_yoda
```

Instead of having the default origin as
```
git remote add origin glblackburn@github.com:glblackburn/pub-bin.git
```
set the origin as below.
```
git remote add origin glblackburn:glblackburn/pub-bin.git
```

# SSH Key Usage Pitfalls

A helpful article about common pitfalls and issues when working with SSH agents.

* https://rabexc.org/posts/pitfalls-of-ssh-agents

This article covers common problems and solutions when using SSH agents, including issues with agent forwarding, key management, and security considerations.

* https://security.stackexchange.com/questions/101783/are-there-any-risks-associated-with-ssh-agent-forwarding

A Stack Exchange discussion about security risks associated with SSH agent forwarding, including potential vulnerabilities and best practices.

* https://infra.apache.org/blog/apache_org_downtime_report.html

A postmortem report from Apache Infrastructure documenting a significant downtime incident. The report includes details about SSH key management issues that contributed to the incident, highlighting the importance of proper SSH key lifecycle management and rotation practices in infrastructure operations.

# Apache Infrastructure Downtime Report

A detailed postmortem report from Apache Infrastructure about a significant downtime incident.

* https://infra.apache.org/blog/apache_org_downtime_report.html

This report provides insights into incident response, root cause analysis, and infrastructure management practices from the Apache Software Foundation.

# Markdown Viewer Chrome Extension

A Chrome browser extension for viewing Markdown files locally with GitHub-flavored Markdown support.

* https://chromewebstore.google.com/detail/markdown-viewer/ckkdlimhmcjmikdlpkmbgfkaikojcbjk

Install the extension from the Chrome Web Store to preview Markdown files directly in your browser. The extension supports GitHub-flavored Markdown syntax and can render local Markdown files.
