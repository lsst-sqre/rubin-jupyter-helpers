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


def get_access_token(tokenfile=None, log=None):
    """Determine the access token from the mounted secret or environment."""
    tok = None
    hdir = os.environ.get("HOME", None)
    if hdir:
        if not tokenfile:
            # FIXME we should make this instance-dependent
            tokfile = hdir + "/.access_token"
        try:
            with open(tokfile, "r") as f:
                tok = f.read().replace("\n", "")
        except Exception as exc:
            if not log:
                log = make_logger()
            log.warn("Could not read tokenfile '{}': {}".format(tokfile, exc))
    if not tok:
        tok = os.environ.get("ACCESS_TOKEN", None)
    return tok


def parse_access_token(endpoint=None, tokenfile=None, token=None, timeout=15):
    """Rely on gafaelfawr to validate and parse the access token."""
    if not token:
        token = get_access_token(tokenfile=tokenfile)
    if not token:
        raise RuntimeError("Cannot determine access token!")
    # Use external endpoint if we know it, otherwise use the internal one,
    #  which should be constant with respect to an origin inside the cluster.
    if not endpoint:
        fqdn = os.getenv("FQDN")
        if not fqdn:
            endpoint = "http://gafaelfawr-service.gafaelfawr:8080/auth/analyze"
        else:
            endpoint = f"https:{fqdn}/gafaelfawr/auth/analyze"
    resp = requests.post(endpoint, data={"token": token}, timeout=timeout)
    rj = resp.json()
    p_resp = rj["token"]
    if not p_resp["valid"]:
        raise RuntimeError("Access token invalid: '{}'!".format(str(resp)))
    # Force to lowercase username (should no longer be necessary)
    p_tok = p_resp["data"]
    uname = p_tok["uid"]
    p_tok["uid"] = uname.lower()
    return p_tok
