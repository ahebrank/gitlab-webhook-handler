import argparse
import json

from .__version__ import (
    __title__,
    __version__
)
from gwh import app
import gwh

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m gwh", description="GitLab webhook handler")
    parser.add_argument("config", help="path to repos configuration")
    parser.add_argument("--version", action="version", version=__title__ + " " + __version__)
    parser.add_argument("--host", help="server host", default="0.0.0.0")
    parser.add_argument("-p", "--port", help="server port", type=int, default=8080)
    parser.add_argument("--allow", help="whitelist GitLab IP block")
    parser.add_argument("--debug", action="store_true", help="enable debug output")

    args = parser.parse_args()

    try:
        gwh.repos = json.loads(open(args.config, encoding='utf-8').read())
    except:
        print("Error opening repos file %s -- check file exists and is valid JSON" % args.config)
        raise

    gwh.whitelist_ip = args.allow

    app.debug = args.debug

    app.run(host=args.host, port=args.port)
