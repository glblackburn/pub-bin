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
