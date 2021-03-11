"""LSST JupyterHub utility classes and functions.
"""

from .groups import (
    get_fake_gid,
    make_passwd_line,
    make_group_lines,
    add_user_to_groups,
    assemble_gids,
    get_supplemental_gids,
    resolve_groups,
)

from .k8s import (
    get_execution_namespace,
    load_k8s_config,
    build_pull_secret,
    get_pull_secret,
    get_pull_secret_reflist,
    ensure_pull_secret,
)

from .log import (
    sanitize_dict,
    make_logger,
)

from .moneypenny import (
    call_moneypenny,
    dossier_from_auth_state,
)

from .token import (
    get_access_token,
    parse_access_token,
)

from .typehelpers import (
    rreplace,
    str_bool,
    str_true,
    listify,
    intify,
    floatify,
    list_duplicates,
    list_digest,
)

from .singleton import Singleton
from ._version import __version__

all = [
    rreplace,
    sanitize_dict,
    get_execution_namespace,
    make_logger,
    str_bool,
    str_true,
    listify,
    intify,
    floatify,
    list_duplicates,
    list_digest,
    get_access_token,
    parse_access_token,
    assemble_gids,
    get_fake_gid,
    make_passwd_line,
    make_group_lines,
    add_user_to_groups,
    get_supplemental_gids,
    resolve_groups,
    load_k8s_config,
    build_pull_secret,
    get_pull_secret,
    get_pull_secret_reflist,
    ensure_pull_secret,
    call_moneypenny,
    Singleton,
    __version__,
]
