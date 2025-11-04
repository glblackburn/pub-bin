## Table of Contents

- [Set different ssh keys for multiple GitHub users](#set-different-ssh-keys-for-multiple-github-users)
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

# Markdown Viewer Chrome Extension

A Chrome browser extension for viewing Markdown files locally with GitHub-flavored Markdown support.

* https://chromewebstore.google.com/detail/markdown-viewer/ckkdlimhmcjmikdlpkmbgfkaikojcbjk

Install the extension from the Chrome Web Store to preview Markdown files directly in your browser. The extension supports GitHub-flavored Markdown syntax and can render local Markdown files.
