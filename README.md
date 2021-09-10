# epsilon.py -- An SVN to Discord Webhook

This is a small Python script that serves to send new SVN commit messages from the
specified SVN server to the given Discord webhook.

* Code (c) 2021 Dino Bollinger, MIT License
* `epsilon.png` taken from the game "Deus Ex"

## Usage

```
usage: epsilon.py [-h] [-u USER] [-p PASSWORD] [-t POLL_TIME] [-n HOOK_NAME] [-a AVATAR] [-l LOGLEVEL] [-i INITIAL_REVISION] svn_url hook_url

epsilon.py -- An SVN to Discord Webhook

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
                        Default is the most recent revision at the time of 
                        connecting to the server.
```