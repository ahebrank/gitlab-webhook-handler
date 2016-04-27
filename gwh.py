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

app = Flask(__name__)
app.debug = os.environ.get('DEBUG') == 'true'

REPOS_JSON_PATH = None
WHITELIST_IP = None

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return 'OK'
    elif request.method == 'POST':
        # Store the IP address of the requester
        request_ip = ipaddress.ip_address(u'{0}'.format(request.remote_addr))

        # Check if the POST request is from github.com or GHE
        if not WHITELIST_IP is None:
            for block in [WHITELIST_IP]:
                if ipaddress.ip_address(request_ip) in ipaddress.ip_network(block):
                    break  # the remote_addr is within the network range of github.
            else:
                abort(403)

        payload = json.loads(request.data)

        if payload['object_kind'] != "push":
            return json.dumps({'msg': "wrong event type"})

        repos = json.loads(io.open(REPOS_JSON_PATH, 'r').read())

        repo_meta = {
            'homepage': payload['repository']['homepage'],
        }

        # Try to match on branch as configured in repos.json
        match = re.match(r"refs/heads/(?P<branch>.*)", payload['ref'])
        if match:
            repo_meta['branch'] = match.groupdict()['branch']
            repo = repos.get(
                '{homepage}/branch:{branch}'.format(**repo_meta), None)

            # Fallback to plain owner/name lookup
            if not repo:
                repo = repos.get('{homepage}'.format(**repo_meta), None)


        if repo.get('action', None):
            for action in repo['action']:
                try:
                    subp = subprocess.Popen(action, cwd=repo.get('path', '.'), shell=True)
                    subp.wait()
                except Exception as e:
                    print e
        return 'OK'


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='gitlab webhook receiver')
    parser.add_argument('-c', '--config', action='store', help='path to repos configuration', required=True)
    parser.add_argument('-p', '--port', action='store', help='server port', required=False, default=8080)
    parser.add_argument('--allow', action='store', help='whitelist Gitlab IP block', required=False)
    args = parser.parse_args()

    port_number = int(args.port)

    REPOS_JSON_PATH = args.config
    WHITELIST_IP = args.ip

    app.run(host='0.0.0.0', port=port_number)
