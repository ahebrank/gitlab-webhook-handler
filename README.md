# Flask webhook for Gitlab

A very simple post-receive web hook handler that executes per default a
pull upon receiving. The executed action is configurable per repository.

It will also optionally verify that the POST request originated from a particular IP address.

## Getting started

### Installation Requirements

Install dependencies found in ``requirements.txt``.

```bash
pip install -r requirements.txt
```

### Repository Configuration

Create a JSON config file (e.g., `repos.json`) to configure repositories. Each repository must be keyed by its Gitlab homepage and optionally by the relevant branch.

```json
{
    "https://gitlab.com/pal/spm-batching/branch:master": {
        "path": "/home/spm-batching",
        "action": ["git pull origin master"],
    }
}
```

### Run

```
python gwh.py --help
```

## Example usage:

Assume a self-hosted Gitlab server on 192.168.1.44 and a production webserver on 192.168.1.99.  The idea is that a push to the master branch for your project should trigger the production machine to pull in a new copy of the repo.

On your webhost (192.168.1.99), bring up the webhook handler:

```
python gwh.py -c repos.json -p 8080 --allow 192.168.1.44 &
```

Then in your Gitlab server (on 192.168.1.44) project settings, create a new webhook with URL http://192.168.1.99:8080 that's triggered on push events.