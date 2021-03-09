"""
Shared utility functions.
"""

import base64
import datetime
import hashlib
import inspect
import json
import logging
import os
import requests
import time

from collections import defaultdict
from eliot.stdlib import EliotHandler
from kubernetes import client
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException
from math import log


def call_moneypenny(dossier, endpoint=None, token=None):
    """Order Moneypenny to commission an agent."""
    if not token:
        # Mint an admin token with the gafaelfawr signing key; see mobu's
        #  User.generate_token()
        token = _mint_token()
    # Use external endpoint if we know it, otherwise use the internal one,
    #  which should be constant with respect to an origin inside the cluster.
    if not mp_endpoint:
        fqdn = os.getenv("FQDN")
        if not fqdn:
            endpoint = f"http://moneypenny.moneypenny:8080/moneypenny"
        else:
            endpoint = f"https:{fqdn}/moneypenny"
    headers = _headers_from_token(token)
    requests.post(f"{endpoint}/commission", data=dossier, timeout=10)
    uname = dossier["username"]
    expiry = datetime.datetime.now() + datetime.timedelta(seconds=300)
    count = 0
    route = f"moneypenny/{uname}"
    while datetime.datetime.now() < expiry:
        count += 1
        resp = requests.get(f"{endpoint}/{uname}")
        status = resp.status
        if status == 200 or 404:
            return
        if status != 202:
            raise RuntimeError(f"Unexpected status from Moneypenny: {status}")
        time.sleep(int(log(count)))
    raise RuntimeError("Moneypenny timed out")


def _mint_token():
    # FIXME
    pass


def _headers_from_token(token):
    # FIXME
    pass
