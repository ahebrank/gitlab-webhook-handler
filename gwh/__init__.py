import re
import json
import subprocess
import ipaddress
from flask import Flask, request, abort
from .gitlab_api import GitlabApi
from .helpers import Helpers

app = Flask(__name__)

whitelist_ip = None
repos = None

@app.route("/", methods=['GET', 'POST'], strict_slashes=False)
def index():
    if request.method == "GET":
        return 'OK'
    elif request.method == "POST":
        # Check the POST source
        if not whitelist_ip is None:
            # Store the IP address of the requester
            request_ip = ipaddress.ip_address(request.remote_addr)

            for block in [whitelist_ip]:
                if request_ip in ipaddress.ip_network(block):
                    break # remote_addr is within the accepted network range
            else:
                abort(403)

        if not len(request.data):
            abort(400)

        try:
            payload = json.loads(request.data)
        except:
            abort(400)

        # common for events
        if payload['object_kind'] in ['push', 'issue']:
            repo_meta = {
                'homepage': payload['repository']['homepage'],
            }
            repo = repos.get(repo_meta['homepage'], None)
            if not repo:
                return "Nothing to do for " + repo_meta['homepage']

            webhook_token = repo.get('webhook_token', None)
            private_token = repo.get('private_token', None)
        else:
            return "Unsupported object kind", 422

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
                            if body_match:
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

