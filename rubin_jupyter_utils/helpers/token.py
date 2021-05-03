"""
Shared utility functions.
"""

import os
import requests
from pathlib import Path


class TokenNotFoundError(Exception):
    """No access token was found."""


def get_access_token(tokenfile=None, log=None):
    """Determine the access token from the mounted configmap (nublado2),
    secret (nublado1), or environment (either).  Prefer the mounted version
    since it can be updated, while the environment variable stays at whatever
    it was when the process was started."""
    tok = None
    if tokenfile:
        # If a path was specified, trust it.
        tok=token_path.read_text(Path(tokenfile))
        tried_path = tokenfile
    else:
        # Try the default token paths, nublado2 first, then nublado1
        n2_tokenfile = "/opt/lsst/software/jupyterlab/environment/ACCESS_TOKEN"
        tried_path=n2_tokenfile
        token_path=Path(n2_tokenfile)
        try:
            tok=token_path.read_text()
        except:
            # Not there.  Let's try the nublado1 path.  Maybe this is an
            #  instance we haven't upgraded yet.  Swallow the exception and
            #  try the older mount.
            pass
        if not tok:
            # We'll try nublado1: ${HOME}/.access_token
            hdir = os.environ.get("HOME", None)
            if hdir:
                tokfile = hdir + "/.access_token"
                tried_path = f"{tried_path}, or {tokfile}"
                token_path=Path(tokfile)
            try:
                tok=token_path.read_text()
            except:
                # OK, it's not mounted at all.  Fall back to the environment.
                pass
    if not tok:
        tok = os.environ.get("ACCESS_TOKEN", None)
    if not tok:
        raise TokenNotFoundError(
            f"Could not find token in env:ACCESS_TOKEN nor in {tried_path}")
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
            endpoint = f"https://{fqdn}/auth/analyze"
    resp = requests.post(endpoint, data={"token": token}, timeout=timeout)
    resp.raise_for_status()
    rj = resp.json()
    p_resp = rj["token"]
    if not p_resp["valid"]:
        raise RuntimeError("Access token invalid: '{}'!".format(str(resp)))
    # Force to lowercase username (should no longer be necessary)
    p_tok = p_resp["data"]
    uname = p_tok["uid"]
    p_tok["uid"] = uname.lower()
    return p_tok
