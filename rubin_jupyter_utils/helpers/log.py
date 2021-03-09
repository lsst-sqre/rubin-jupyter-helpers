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


def sanitize_dict(input_dict, sensitive_fields):
    """Remove sensitive content.  Useful for logging."""
    retval = {}
    if not input_dict:
        return retval
    retval.update(input_dict)
    for field in sensitive_fields:
        if retval.get(field):
            retval[field] = "[redacted]"
    return retval


def make_logger(name=None, level=None):
    """Create a logger with LSST-appropriate characteristics."""
    if name is None:
        # Get name of caller's class.
        #  From https://stackoverflow.com/questions/17065086/
        frame = inspect.stack()[1][0]
        name = _get_classname_from_frame(frame)
    logger = logging.getLogger(name)
    if name is None:
        logger.info("jupyterhubutils make_logger() called for root logger.")
        logger.info("not eliotify-ing root logger.")
        return logger
    logger.propagate = False
    if level is None:
        level = logging.getLogger().getEffectiveLevel()
    logger.setLevel(level)
    logger.handlers = [EliotHandler()]
    logger.info("Created logger object for class '{}'.".format(name))
    return logger


def _get_classname_from_frame(fr):
    args, _, _, value_dict = inspect.getargvalues(fr)
    # we check the first parameter for the frame function is
    # named 'self'
    if len(args) and args[0] == "self":
        # in that case, 'self' will be referenced in value_dict
        instance = value_dict.get("self", None)
        if instance:
            # return its classname
            cl = getattr(instance, "__class__", None)
            if cl:
                return "{}.{}".format(cl.__module__, cl.__name__)
    # If it wasn't a class....
    return "<unknown>"
