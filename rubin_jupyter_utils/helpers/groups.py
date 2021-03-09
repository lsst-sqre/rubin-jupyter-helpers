"""
Shared utility functions.
"""

import hashlib


def get_fake_gid(grpname):
    """Use if we have strict_ldap_groups off, to assign GIDs to names
    with no matching Unix GID.  We would like them to be consistent, so
    we will use a hash of the group name, modulo some large-ish constant,
    added to another large-ish constant.

    There is a chance of collision, but it doesn't really matter.

    We do need to keep the no-GID groups around, though, because we might
    be using them to make options form or quota decisions (if we know we
    don't, we should turn on strict_ldap_groups).
    """
    grpbase = 3e7
    grprange = 1e7
    grphash = hashlib.sha256(grpname.encode("utf-8")).hexdigest()
    grpint = int(grphash, 16)
    igrp = int(grpbase + (grpint % grprange))
    return igrp


def make_passwd_line(claims):
    """Create an entry for /etc/passwd based on our claims.  Returns a
    newline-terminated string.
    """
    uname = claims["uid"]
    uid = claims["uidNumber"]
    pwline = "{}:x:{}:{}::/home/{}:/bin/bash\n".format(uname, uid, uid, uname)
    return pwline


def assemble_gids(claims, strict_ldap=False):
    """Take the claims data and return the string to be used for be used
    for provisioning the user and groups (in sudo mode).
    """
    glist = _map_supplemental_gids(claims, strict_ldap=strict_ldap)
    gidlist = ["{}:{}".format(x[0], x[1]) for x in glist]
    return ",".join(gidlist)


def make_group_lines(claims, strict_ldap=False):
    """Create a list of newline-terminated strings representing group
    entries suitable for appending to /etc/group.
    """
    uname = claims["uid"]
    uid = claims["uidNumber"]
    # Add individual group; don't put user in it (implicit from group in
    #  passwd)
    glines = ["{}:x:{}:\n".format(uname, uid)]
    glist = _map_supplemental_gids(claims, strict_ldap=strict_ldap)
    glines.extend(["{}:x:{}:{}\n".format(x[0], x[1], uname) for x in glist])
    return glines


def get_supplemental_gids(claims, strict_ldap=False):
    """Create a list of gids suitable to paste into the supplemental_gids
    the container can run with (in sudoless mode)."""
    glist = _map_supplemental_gids(claims, strict_ldap=strict_ldap)
    return [x[1] for x in glist]


def resolve_groups(claims, strict_ldap=False):
    """Returns groupmap suitable for insertion into auth_state;
    group values are strings.
    """
    glist = _map_supplemental_gids(claims, strict_ldap=strict_ldap)
    groupmap = {}
    for gt in glist:
        groupmap[gt[0]] = str(gt[1])
    return groupmap


def _map_supplemental_gids(claims, strict_ldap=False):
    """Helper function to deal with group manipulation.  Returns a list of
    tuples (groupname, gid).

    If a name has no id, omit the entry if strict_ldap is True.  Otherwise
    generate a fake gid for it and use that.
    """
    uname = claims["uid"]
    groups = claims["isMemberOf"]
    retval = []
    for grp in groups:
        gname = grp["name"]
        if gname == uname:
            continue  # We already have private group as runAsGid
        gid = grp.get("id", None)
        if not gid:
            if not strict_ldap:
                gid = get_fake_gid(gname)
        if gid:
            retval.append((gname, gid))
    return retval


def add_user_to_groups(uname, grpstr, groups=["lsst_lcl", "jovyan"]):
    """Take a user name (a string) and a base group file (as a string) and
    inject the user into the appropriate groups, given in the groups
    parameter (defaults to 'lsst_lcl' and 'jovyan').  Returns a string."""
    glines = grpstr.split("\n")
    g_str = ""
    for grp in glines:
        s_line = grp.strip()
        if not s_line:
            continue
        grpname = s_line.split(":")[0]
        if grpname in groups:
            if s_line.endswith(":"):
                s_line = s_line + uname
            else:
                s_line = s_line + "," + uname
        g_str = g_str + s_line + "\n"
    return g_str
