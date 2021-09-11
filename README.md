# epsilon.py -- An SVN to Discord Webhook Pipe

This is a small Python script that serves to send new SVN commit strings from the
specified SVN server to the given Discord webhook. This commit string includes 
revision number, author, datetime, files changed, and commit message.

Example:
```
r12 | dino.bollinger | 2021-09-10 21:08:55 +0000 (Fri, 10 Sep 2021) | 1 line
-----------------------------------------------------------------------
Changed paths:
A | /LICENSE
M | /README.md
-----------------------------------------------------------------------
Commit message:
    Update the README and add a LICENSE file
```

* Code (c) 2021 Dino Bollinger, MIT License
* `epsilon.png` taken from the game "Deus Ex"

## Requirements

Tested with:
* `Python 3.8.3`

Libraries:
* `svn 1.0.1+`
* `dhooks 1.1.4+`

And assuming Discord doesn't alter the webhook API.

## Usage

Running the following command on a public SVN will be enough to post commits to a Discord channel:

```
./epsilon.py <svn_url> <hook_url>
```

If the SVN needs authentication, this can be specified using the `-u` and `-p` parameters for user and password respectively.

If the script is shut down unexpectedly, it will write the last known revision number to `./.epsilon_last_revision`. 
On restart, it will resume from the revision found in this file. If it is not present, it will simply start from the 
latest revision reported by the SVN server.

If you need to start from a specific revision, you can either specify the `-i` parameter, or alter the value stored in 
the file `./.epsilon_last_revision`.

## Parameters

```
usage: epsilon.py [-h] [-u USER] [-p PASSWORD] [-t POLL_TIME] [-n HOOK_NAME] [-a AVATAR] [-l LOGLEVEL] [-i INITIAL_REVISION] svn_url hook_url

epsilon.py -- An SVN to Discord Webhook Pipe

positional arguments:
  svn_url               URL that points to the SVN repository
  hook_url              URL that points to the Discord webhook

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  SVN user account, if required. "None" by default.
  -p PASSWORD, --password PASSWORD
                        SVN password, if required. "None" by default.
  -t POLL_TIME, --poll_time POLL_TIME
                        Delay for polling SVN, in seconds. Default is 120
  -n HOOK_NAME, --hook_name HOOK_NAME
                        Name for the webhook bot when posting. Default is "Epsilon"
  -a AVATAR, --avatar AVATAR
                        Filepath for the webhook avatar. Default is "./epsilon.png"
  -l LOGLEVEL, --loglevel LOGLEVEL
                        Log level for the log file. Default is "Warning"
  -i INITIAL_REVISION, --initial_revision INITIAL_REVISION
                        Initial revision number to start from. 
                        Can be used to print existing revisions to the channel. 
```
