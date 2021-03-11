"""
Shared utility functions.
"""

import base64
import json
import os

from kubernetes import client
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException

from .log import make_logger


def get_execution_namespace():
    """Return Kubernetes namespace of this container."""
    ns_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"
    if os.path.exists(ns_path):
        with open(ns_path) as f:
            return f.read().strip()
    return None


def load_k8s_config(log=None):
    try:
        load_incluster_config()
    except ConfigException:
        if not log:
            log = make_logger()
        log.warning("In-cluster config failed! Falling back to kube config.")
        try:
            load_kube_config()
        except ValueError as exc:
            log.error("Failed to load k8s config: {}".format(exc))
            raise


def build_pull_secret(
    username, password, host=None, pull_secret_name="pull-secret"
):
    if not (username and password):
        return None  # These do not exist unless we have both auth parts
    # Use "registry.hub.docker.com" as canonical.
    if not host or host == "docker.io" or host == "index.docker.io":
        host = "registry.hub.docker.com"
    basic_auth = "{}:{}".format(username, password).encode("utf-8")
    authdata = {
        "auths": {
            host: {
                "username": username,
                "password": password,
                "auth": base64.b64encode(basic_auth).decode("utf-8"),
            }
        }
    }
    b64authdata = base64.b64encode(
        json.dumps(authdata).encode("utf-8")
    ).decode("utf-8")
    pull_secret = client.V1Secret()
    pull_secret.metadata = client.V1ObjectMeta(name=pull_secret_name)
    pull_secret.type = "kubernetes.io/dockerconfigjson"
    pull_secret.data = {".dockerconfigjson": b64authdata}
    return pull_secret


def get_pull_secret(pull_secret_name="pull-secret", api=None, log=None):
    if not pull_secret_name:
        return
    ns = get_execution_namespace()
    secret = None
    if not api:
        load_k8s_config()
        api = CoreV1Api()
    try:
        secret = api.read_namespaced_secret(pull_secret_name, ns)
    except ApiException as e:
        if not log:
            log = make_logger()
        log.error(
            f"Couldn't read secret {pull_secret_name} "
            + f" in namespace {ns}: {e}"
        )
        raise
    return secret


def get_pull_secret_reflist(pull_secret_name="pull-secret"):
    if not pull_secret_name:
        return []
    pull_secret_ref = client.V1LocalObjectReference(name=pull_secret_name)
    return [pull_secret_ref]


def ensure_pull_secret(
    secret, namespace=get_execution_namespace(), api=None, log=None
):
    if not secret:
        return
    if not api:
        load_k8s_config()
        api = CoreV1Api()
    try:
        name = secret.metadata.name
        # Give secret new metadata; lots of read-only stuff in the existing
        #  secret metadata.
        secret.metadata = client.V1ObjectMeta(name=name, namespace=namespace)
        api.create_namespaced_secret(namespace=namespace, body=secret)
    except ApiException as e:
        if not log:
            log = make_logger()
        if e.status != 409:
            log.error("Failed to create pull secret: {}".format(e))
            raise
        log.info(f"Pull secret already exists in namespace {namespace}")
