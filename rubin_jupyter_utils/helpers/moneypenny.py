"""
Shared utility functions.
"""

import datetime
import jwt
import os
import requests
import time

from math import log
from string import Template

FQDN = os.getenv("FQDN")


def call_moneypenny(
    dossier,
    endpoint=None,
    token=None,
    template_file=None,
    private_key_file=None,
    url=None,
):
    """Order Moneypenny to commission an agent."""
    if not token:
        # Mint an admin token with the gafaelfawr signing key; see mobu's
        #  User.generate_token()
        token = _mint_moneypenny_token(
            template_file=template_file,
            private_key_file=private_key_file,
            url=url,
        )
    # Use external endpoint if we know it, otherwise use the internal one,
    #  which should be constant with respect to an origin inside the cluster.
    if not endpoint:
        if not FQDN:
            endpoint = "http://moneypenny.moneypenny:8080/moneypenny"
        else:
            endpoint = f"https:{FQDN}/moneypenny"
    headers = {"X-Auth-Request-Token": f"Bearer {token}"}
    requests.post(
        f"{endpoint}/commission", data=dossier, headers=headers, timeout=10
    )
    uname = dossier["username"]
    expiry = datetime.datetime.now() + datetime.timedelta(seconds=300)
    count = 0
    route = f"moneypenny/{uname}"
    while datetime.datetime.now() < expiry:
        count += 1
        resp = requests.get(f"{endpoint}/{uname}", headers=headers)
        status = resp.status
        if status == 200 or 404:
            return
        if status != 202:
            raise RuntimeError(f"Unexpected status from Moneypenny: {status}")
        time.sleep(int(log(count)))
    raise RuntimeError("Moneypenny timed out")


def _mint_moneypenny_token(
    template_file=None, private_key_file=None, url=None
):
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
        "environment_url": Configuration.environment_url,
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
