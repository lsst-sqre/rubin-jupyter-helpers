"""
Shared utility functions.
"""

import datetime
import json
import jwt
import math
import os
import requests
import time

from string import Template

from .log import make_logger

FQDN = os.getenv("FQDN")


def call_moneypenny(
    dossier,
    endpoint=None,
    token=None,
    template_file=None,
    private_key_file=None,
    url=None,
    log=None,
):
    """Order Moneypenny to commission an agent."""
    if not log:
        log = make_logger()
    if not token:
        # Mint an admin token with the gafaelfawr signing key; see mobu's
        #  User.generate_token()
        token = _mint_moneypenny_token(
            template_file=template_file,
            private_key_file=private_key_file,
            url=url,
            log=log,
        )
    # Use external endpoint if we know it, otherwise use the internal one,
    #  which should be constant with respect to an origin inside the cluster.
    if not endpoint:
        if not FQDN:
            endpoint = "http://moneypenny.moneypenny:8080/moneypenny"
        else:
            endpoint = f"https://{FQDN}/moneypenny"
    headers = {"Authorization": f"Bearer {token}"}
    com_ep = f"{endpoint}/commission"
    log.debug(f"About to post to {com_ep}: {dossier}.")
    resp = requests.post(
        f"{com_ep}", json=dossier, headers=headers, timeout=10
    )
    log.debug(f"POST got {resp.status_code}")
    resp.raise_for_status()
    uname = dossier["username"]
    expiry = datetime.datetime.now() + datetime.timedelta(seconds=300)
    count = 0
    route = f"moneypenny/{uname}"
    while datetime.datetime.now() < expiry:
        count += 1
        st_ep = f"{endpoint}/{uname}"
        log.debug(f"Checking Moneypenny status at {st_ep}: #{count}")
        resp = requests.get(f"{st_ep}", headers=headers)
        status = resp.status_code
        log.debug(f"Moneypenny status: {status}")
        if status == 200 or 404:
            return
        if status != 202:
            raise RuntimeError(f"Unexpected status from Moneypenny: {status}")
        time.sleep(int(math.log(count)))
    raise RuntimeError("Moneypenny timed out")


def _mint_moneypenny_token(
    template_file=None, private_key_file=None, url=None, log=None
):
    if not log:
        log = make_logger()
    if not url:
        if not FQDN:
            raise RuntimeError(
                "Could not determine URL for Moneypenny admin token"
            )
        url = f"https://{FQDN}"
    if not template_file:
        template_file = os.path.join(
            os.path.dirname(__file__), "static/moneypenny-jwt-template.json"
        )
    with open(template_file, "r") as f:
        token_template = Template(f.read())

    if not private_key_file:
        private_key_file = "/etc/keys/signing_key.pem"
    with open(private_key_file, "r") as f:
        signing_key = f.read()

    current_time = int(time.time())

    token_data = {
        "environment_url": url,
        "username": "moneypenny",
        "uidnumber": 1007,
        "issue_time": current_time,
        "expiration_time": current_time + 300,
    }

    token_dict = json.loads(token_template.substitute(token_data))
    token = jwt.encode(
        token_dict,
        key=signing_key,
        headers={"kid": "reissuer"},
        algorithm="RS256",
    )
    return token


def dossier_from_auth_state(auth_state, log=None):
    if not log:
        log = make_logger()
    clm = auth_state["claims"]
    log.debug(
        "Auth state claims: " + json.dumps(clm, indent=4, sort_keys=True)
    )
    dossier = {
        "username": clm["uid"],
        "uid": int(clm["uidNumber"]),
        "groups": [x for x in clm["isMemberOf"]],
    }
    log.debug("Dossier: " + json.dumps(dossier, indent=4, sort_keys=True))
    return dossier
