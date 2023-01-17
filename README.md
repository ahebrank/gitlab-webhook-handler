# Flask webhook for GitLab

A very simple post-receive web hook handler for GitLab based on a project for Github: [razius/github-webhook-handler](https://github.com/razius/github-webhook-handler)

It will optionally verify that the POST request originated from a particular IP address.

## Getting started

### Installation

```bash
pip install gwh
```

### Repository Configuration

Create a JSON config file (e.g., `repos.json`) to configure repositories. Each repository must be keyed by its GitLab homepage.

```json
{
    "https://gitlab.com/pal/spm-batching": {
        "private_token": "xxxxxxxxxxxxx",
        "webhook_token": "xxxxxxxxxxxxx",
        "push": {
            "master": {
                "path": "/home/spm-batching/deploy",
                "actions": [
                  "git checkout master",
                  "git pull"
                ]
            },
            "other": {
                "actions": [
                    "echo A non-master branch was pushed."
                ]
            }
        }
    },
        "issue": {
            "user_notify": [
                "\\*\\*Sender\\*\\*\\: ([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+)",
                "@gitlabuser"
            ],
            "labels": []
        }
    }
}
```

This example handles several types of webhooks.

1. `push`: After a push event to the repo `master` branch, it executes a couple of command in the local shell to pull in the master HEAD. The special branch key `other` will run if the pushed branch is not otherwise matched to a key in the `push` hash.
2. `issue.user_notify`: After a new issue event, the handler runs a regex match on the issue body and adds an issue comment to @mention the user by email.
3. `issue.labels`: Parse the commit message to handle adding or removing labels based on commit messages. For instance, "address #53, #72: carousel accessibility fixes; -browser compat, +accessibility, ~Pending" will add an "accessibility" label (if it already exists for the project) to issues 53 and 72, remove label "browser compat", and add label "Pending" (presumably a list label) while removing other list labels (effectively moving an issue on the GitLab boards kanban).

The issue hook uses a [GitLab personal access token](https://docs.gitlab.com/ee/api/#personal-access-tokens) (`private_token`) to run API commands to lookup a username by email and add an issue comment. The push hook does not require the private token because it does not use the GitLab API.

`webhook_token` allows authorization by matching against a [secret token included in the payload headers](https://docs.gitlab.com/ce/user/project/integrations/webhooks.html#secret-token).

### Run

```
python -m gwh --help
```

## Example usage:

Assume a self-hosted GitLab server on 192.168.1.44 and a production webserver on 192.168.1.99.  The idea is that a push to the master branch for your project should trigger the production machine to pull in a new copy of the repo.

On your webhost (192.168.1.99), bring up the webhook handler:

```
python -m gwh -p 8080 --allow 192.168.1.44 repos.json &
```

Then in your GitLab server (on 192.168.1.44) project settings, create a new webhook with URL http://192.168.1.99:8080 that's triggered on push events.

## Test

```
curl -i -X POST -H "Content-Type: application/json" --data "@test.json" http://localhost:8080
```

