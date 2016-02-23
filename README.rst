Flask webhook for Gitlab
########################
A very simple post-receive web hook handler that executes per default a
pull uppon receiving. The executed action is configurable per repository.

It will also optionally verify that the POST request originated from a particular IP address.

Getting started
----------------

Installation Requirements
=========================

Install dependencies found in ``requirements.txt``.

.. code-block:: console

    pip install -r requirements.txt

Repository Configuration
========================

Edit ``repos.json`` to configure repositories. Each repository must be keyed by its Gitlab homepage and optionally by the relevant branch.


.. code-block:: json

    {
        "https://gitlab.com/pal/spm-batching/branch:master": {
            "path": "/home/spm-batching",
            "action": ["git pull origin master"],
        }
    }

Runtime Configuration
=====================

.. code-block:: console

    python gwh.py --help