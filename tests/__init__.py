"""Test suite for whobuilt. Standard library only, like the tool itself.

Nothing here touches the network: any attempt to open a socket fails loudly, so a test
that forgets to mock a registry or GitHub call breaks instead of quietly passing.

    python -m unittest discover -s tests -v
"""

import socket


class _NetworkBlocked(RuntimeError):
    pass


def _no_network(*args, **kwargs):
    raise _NetworkBlocked("tests must not use the network; mock whobuilt.resolve._get")


socket.socket.connect = _no_network
socket.socket.connect_ex = _no_network
socket.create_connection = _no_network
