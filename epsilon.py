#!/bin/python3
# Copyright (c) 2021 Dino Bollinger
# MIT License
"""
epsilon.py -- An SVN to Discord Webhook Pipe
"""

import argparse
import os
import logging
from datetime import datetime
import time
import traceback

from dhooks import Webhook
import svn.remote
import svn.exception

hook_commit_dateformat = "%Y-%m-%d %H:%M:%S %z (%a, %d %b %Y)"
commit_header_template = "r{revision} | {author} | {cdate} | {linecount} {linestr}"
commit_modeline_template = "{mode} | {filepath}"
commit_template = "```\n{header}\n{separator}\nChanged paths:\n{changes}\n{separator}\nCommit message:\n{message}\n```"

CHAR_THRESHOLD = 1900
ABSOLUTE_LIMIT = 2000

rev_file = "./.epsilon_last_revision"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svn_url', type=str, help='URL that points to the SVN repository')
    parser.add_argument('hook_url', type=str, help='URL that points to the Discord webhook')

    parser.add_argument('-u', '--user', type=str, default=None,
                        help='SVN user account, if required. "None" by default.')
    parser.add_argument('-p', '--password', type=str, default=None,
                        help='SVN password, if required. "None" by default.')
    parser.add_argument('-t', '--poll_time', type=int, default=120,
                        help='Delay for polling SVN, in seconds. Default is 120')
    parser.add_argument('-n', '--hook_name', type=str, default="Epsilon",
                        help='Name for the webhook bot when posting. Default is "Epsilon"')
    parser.add_argument('-a', '--avatar', type=str, default="./epsilon.png",
                        help='Filepath for the webhook avatar. Default is "./epsilon.png"')
    parser.add_argument('-l', '--loglevel', type=str, default="WARNING",
                        help='Log level for the log file. Default is "Warning"')
    parser.add_argument('-i', '--initial_revision', type=int, default=None,
                        help='Initial revision number to start from. Will print all commits up to most recent.')
    args = parser.parse_args()

    # Set up logger
    logger = logging.getLogger('epsilon')
    logger.setLevel(logging.DEBUG)

    # Add filehandler
    dt_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    fh = logging.FileHandler(f"/tmp/epsilon_{dt_string}.log", mode='w')
    fh.setFormatter(logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt='%m-%d %H:%M'))
    fh.setLevel(logging.getLevelName(args.loglevel))
    logger.addHandler(fh)

    # Add streamhandler
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)

    # try load PFP
    pfp_img = None
    if os.path.exists(args.avatar):
        with open(args.avatar, 'rb') as fd:
            pfp_img = fd.read()
    else:
        logger.warning(f"Webhook avatar '{args.avatar}' not found!")

    # Connect to SVN
    svn_client = svn.remote.RemoteClient(args.svn_url, username=args.user, password=args.password)
    if not svn_client:
        logger.error("Connection to SVN failed. Aborting webhook script...")
        return 1
    logger.info("Connection to SVN successful.")
    logger.info(f"Polling SVN at an interval of {args.poll_time} seconds")

    svn_startup_info = svn_client.info()
    c_rev: int
    if args.initial_revision:
        logger.info("Using specified initial revision...")
        c_rev = args.initial_revision
    elif os.path.exists(rev_file):
        logger.info("Loading last know revision from file...")
        with open(rev_file, 'r') as fd:
            c_rev = int(fd.read())
    else:
        logger.info("Using HEAD as latest revision...")
        c_rev = svn_startup_info["commit_revision"]

    p_rev: int = c_rev
    ls_rev: int = c_rev

    logger.info(f"Initial revision: {c_rev}")

    # Connect to Webhook
    hook = Webhook(args.hook_url)
    if not hook:
        logger.error("Connection to Discord webhook failed. Aborting webhook script...")
        return 2
    logger.info("Connection to Webhook successful.")

    hook.modify(name=args.hook_name, avatar=pfp_img)

    try:
        logger.info("Epsilon webhook initiated.")
        delay_increment = 0
        while True:
            try:
                c_rev = svn_client.info()["commit_revision"]

                # print log messages and diffs
                if c_rev > p_rev:
                    logger.info(f"Found {c_rev - p_rev} new commit(s) to send to webhook.")
                    all_logs = svn_client.log_default(revision_from=p_rev + 1, revision_to=c_rev, changelist=True)
                    for log in all_logs:
                        total_msg_length = 50
                        commit_time = log.date.strftime(hook_commit_dateformat)
                        commit_linecount = 0 if not log.msg else log.msg.count('\n') + 1
                        linestr = "line" if commit_linecount == 1 else "lines"
                        commit_header = commit_header_template.format(revision=log.revision, author=log.author,
                                                                      linestr=linestr,
                                                                      cdate=commit_time, linecount=commit_linecount)
                        total_msg_length += len(commit_header)

                        commit_separator = "-" * len(commit_header)
                        total_msg_length += 2 * len(commit_separator)

                        commit_message = ""
                        if log.msg:
                            i = 0
                            message_linecount = len(log.msg.split("\n"))
                            for m in log.msg.split("\n"):
                                if (total_msg_length + (len(m) + 5) > CHAR_THRESHOLD):
                                    omit_msg = f"...({message_linecount - i} lines omitted)\n"
                                    if (total_msg_length + len(omit_msg) > ABSOLUTE_LIMIT):
                                        break
                                    commit_message += omit_msg
                                    total_msg_length += len(omit_msg)
                                    break
                                total_msg_length += (len(m) + 5)
                                commit_message += " " * 4
                                commit_message += m
                                commit_message += "\n"
                                i += 1


                        commit_changes = ""
                        message_linecount = len(log.changelist)
                        if (total_msg_length < CHAR_THRESHOLD):
                            i = 0
                            for c in log.changelist:
                                changeline = commit_modeline_template.format(mode=c[0], filepath=c[1])
                                if (total_msg_length + len(changeline) > CHAR_THRESHOLD):
                                    omit_msg = f"...({message_linecount - i} lines omitted)\n"
                                    if (total_msg_length + len(omit_msg) > ABSOLUTE_LIMIT):
                                        break
                                    commit_changes += omit_msg
                                    total_msg_length += len(omit_msg)
                                    break
                                total_msg_length += len(changeline)
                                commit_changes += changeline
                                commit_changes += "\n"
                                i += 1
                            commit_changes = commit_changes[0:-1]
                        else:
                            omit_msg = f"...({message_linecount - i} lines omitted)\n"
                            if (total_msg_length + len(omit_msg) < ABSOLUTE_LIMIT):
                                commit_changes += omit_msg
                                total_msg_length += len(omit_msg)

                        new_commit_string = commit_template.format(header=commit_header, separator=commit_separator,
                                                                   changes=commit_changes, message=commit_message)

                        # This will block here until connection can be established
                        logger.debug(new_commit_string + "\n")
                        hook.send(content=new_commit_string)
                        ls_rev = log.revision
                        time.sleep(1)

                    with open(rev_file, 'w') as fd:
                        fd.write(f"{c_rev}")
                    logger.info(f"New HEAD revision: r{c_rev}")
            except svn.exception.SvnException:
                logger.error(f"Error contacting SVN server: '{args.svn_url}'")
                logger.error(f"Traceback: {traceback.format_exc()}")
                delay_increment = min(delay_increment + 15, 120)
            else:
                delay_increment = 0
                p_rev = c_rev

            time.sleep(args.poll_time + delay_increment)
    except KeyboardInterrupt:
        logger.info("Shutting down webhook...")
        hook.close()
        exitcode = 0
    except Exception:
        logger.error(f"An unknown error occurred, shutting down server.")
        logger.error(f"Traceback: {traceback.format_exc()}")
        exitcode = -1

    # write last good revision
    with open(rev_file, 'w') as fd:
        fd.write(f"{ls_rev}")

    return exitcode

if __name__ == "__main__":
    exit(main())
