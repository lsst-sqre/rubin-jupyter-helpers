"""
Shared utility functions.
"""

import inspect
import logging

from eliot.stdlib import EliotHandler


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
