#!/usr/bin/env python
import io
import os
import re
import sys
import json
import subprocess
import requests
import ipaddress
from flask import Flask, request, abort
import argparse
from gitlab_api import GitlabApi
from helpers import Helpers

app = Flask(__name__)

REPOS_JSON_PATH = None
WHITELIST_IP = None
repos = None

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        return 'OK'
    elif request.method == "POST":
        # Store the IP address of the requester
        request_ip = ipaddress.ip_address(u'{0}'.format(request.remote_addr))

        # Check the POST source
        if not WHITELIST_IP is None:
            for block in [WHITELIST_IP]:
                if ipaddress.ip_address(request_ip) in ipaddress.ip_network(block):
                    break  # the remote_addr is within the network range of github.
            else:
                abort(403)

        payload = json.loads(request.data)

        # common for events
        if payload['object_kind'] in ['push', 'issue']:
            repo_meta = {
                'homepage': payload['repository']['homepage'],
            }
            repo = repos.get(repo_meta['homepage'], None)
            private_token = repo.get('private_token', None)
            webhook_token = repo.get('webhook_token', None)
        else:
            return "Unsupported object kind", 501

        if not repo:
            return "Nothing to do for " + repo_meta['homepage']

        if webhook_token:
            # validate against X-Gitlab-Token header
            request_token = request.headers.get('X-Gitlab-Token', None)
            if not request_token or request_token != webhook_token:
                abort(403)

        if payload['object_kind'] == "push":
            match = re.match(r"refs/heads/(?P<branch>.*)", payload['ref'])
            if match:
                repo_meta['branch'] = match.groupdict()['branch']
            else:
                return "Unable to determine pushed branch"

            push = repo.get("push", None)
            if push:
                branch = push.get(repo_meta['branch'], None)
                if not branch:
                    branch = repo['push'].get("other", None)
                if branch:
                    branch_actions = branch.get("actions", None)

                    if branch_actions:
                        for action in branch_actions:
                            try:
                                subp = subprocess.Popen(action, cwd=branch.get("path", "."), shell=True)
                                subp.wait()
                            except Exception as e:
                                print(e)
            return 'OK'

        if payload['object_kind'] == "issue":
            issue = repo.get("issue", None)
            if issue:
                private_token = repo.get('private_token', None)
                # notification for new issue
                if issue.get("user_notify", None) and payload['object_attributes']['action'] == "open":
                    if not private_token:
                        abort(403)
                    gl = GitlabApi(repo_meta['homepage'], private_token)
                    notify = issue['user_notify']
                    description = payload['object_attributes']['description']
                    usernames = []
                    for n in notify:
                        username_match = re.match("^@[a-zA-Z0-9_.+-]+$", n)
                        if username_match:
                            # simple username
                            usernames.append(n)
                        else:
                            # try to pull the email from the issue body
                            # and derive the username from that
                            body_match = re.match(n, description)
                            if body_match and private_token:
                                email = body_match.group(1)
                                username = gl.lookup_username(email)
                                if username:
                                    usernames.append("@" + username)
                    # narrow down to unique names
                    usernames = list(set(usernames))
                    if len(usernames) > 0:
                        project_id = payload['object_attributes']['project_id']
                        issue_id = payload['object_attributes']['id']
                        gl.comment_on_issue(project_id, issue_id, "Automatic mention for %s" % (" and ".join(usernames)))

                # parse commit message and manage labels on issues
                if issue.get("labels"):
                    if not private_token:
                        abort(403)
                    gl = GitlabApi(repo_meta['homepage'], private_token)
                    helpers = Helpers()
                    project_id = payload['object_attributes']['project_id']
                    labels = helpers.get_label_names(gl.get_labels(project_id))
                    list_labels = helpers.get_list_labels(gl.get_boards(project_id))
                    for commit in payload['commits']:
                        parse_commit = helpers.parse_commit_labels(commit['message'])
                        for issue in parse_commit['issues']:
                            issue_labels = gl.get_issue(project_id, issue)
                            updated_labels = helpers.simplify_labels(issue_labels, parse_commit['label_ops'])
                            gl.set_issue_labels(project_id, issue, updated_labels)
            return 'OK'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gitlab webhook receiver")
    parser.add_argument("-c", "--config", action="store",
                        help="path to repos configuration", required=True)
    parser.add_argument("-p", "--port", action="store", help="server port",
                        required=False, default=8080)
    parser.add_argument("--allow", action="store", help="whitelist Gitlab IP block",
                        required=False, default=None)
    parser.add_argument("--debug", action="store_true", help="enable debug output",
                        required=False, default=False)

    args = parser.parse_args()
    port_number = int(args.port)

    REPOS_JSON_PATH = args.config
    try:
        repos = json.loads(io.open(REPOS_JSON_PATH, 'r').read())
    except:
        print("Error opening repos file %s -- check file exists and is valid json" % REPOS_JSON_PATH)
        raise

    if args.allow:
        WHITELIST_IP = unicode(args.allow, "utf-8")

    if args.debug:
        app.debug = True

    app.run(host="0.0.0.0", port=port_number)
