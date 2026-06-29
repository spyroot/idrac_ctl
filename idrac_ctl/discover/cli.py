"""Console entry point for ``redfish-discover``.

This wires the pure pieces (:func:`idrac_ctl.discover.classifier.classify_vendor`
and :func:`idrac_ctl.discover.scanner.scan_subnet`) into a CLI and renders the
results as a table. Rendering prefers ``rich`` when it is importable and the
output is a real terminal; otherwise it falls back to a fixed-width plain-text
table so the tool works in pipes, logs, and CI.

The default network fetcher is intentionally a stub that returns no services:
real discovery requires a transport/auth policy the operator supplies. Keeping
the default inert means importing or invoking this module never opens a socket
and never uses credentials, which is what lets the rest of the package stay
offline-testable.

Author Mus spyroot@gmail.com
"""
import argparse
import asyncio
import sys
from typing import Any, Dict, List, Optional, Sequence, TextIO

from idrac_ctl.discover.scanner import DiscoveredService, scan_subnet

# Column order for both renderers; (header, record-key) pairs.
_COLUMNS = (
    ("IP", "ip"),
    ("Vendor", "vendor"),
    ("Product", "product"),
    ("Redfish", "redfish_version"),
)


def _supports_rich(stream: TextIO) -> bool:
    """Return True when ``rich`` is importable and ``stream`` is a TTY.

    Both conditions matter: ``rich`` styling is only worth using on an
    interactive terminal, and on a non-TTY (pipe/file/CI) we degrade to plain
    text so escape codes never pollute the output.
    """
    if not _stream_is_tty(stream):
        return False
    try:
        import rich  # noqa: F401
    except ImportError:
        return False
    return True


def _stream_is_tty(stream: TextIO) -> bool:
    """Best-effort ``isatty`` check that tolerates odd stream objects."""
    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except Exception:
        return False


def _cell(record: Dict[str, Any], key: str) -> str:
    """Stringify one record cell, rendering missing values as ``-``."""
    value = record.get(key)
    return "-" if value is None else str(value)


def render_table(
        services: Sequence[DiscoveredService],
        stream: Optional[TextIO] = None) -> None:
    """Render discovered services to ``stream`` (default ``sys.stdout``).

    Uses ``rich`` when available on a TTY; otherwise writes a plain-text table.
    An empty result set prints a short notice rather than an empty frame.
    """
    out = stream if stream is not None else sys.stdout
    records = [svc.as_dict() for svc in services]

    if not records:
        out.write("No Redfish services discovered.\n")
        return

    if _supports_rich(out):
        _render_rich(records, out)
    else:
        _render_plain(records, out)


def _render_rich(records: List[Dict[str, Any]], out: TextIO) -> None:
    """Render with ``rich`` (only called when import + TTY checks passed)."""
    from rich.console import Console
    from rich.table import Table

    table = Table(title="Discovered Redfish services")
    for header, _key in _COLUMNS:
        table.add_column(header)
    for record in records:
        table.add_row(*(_cell(record, key) for _header, key in _COLUMNS))

    Console(file=out).print(table)


def _render_plain(records: List[Dict[str, Any]], out: TextIO) -> None:
    """Render a fixed-width plain-text table (no escape codes)."""
    headers = [header for header, _key in _COLUMNS]
    keys = [key for _header, key in _COLUMNS]

    rows = [[_cell(record, key) for key in keys] for record in records]
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows))
        for i in range(len(headers))
    ]

    def _fmt(cells: Sequence[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    out.write(_fmt(headers) + "\n")
    out.write(_fmt(["-" * w for w in widths]) + "\n")
    for row in rows:
        out.write(_fmt(row) + "\n")


async def _default_get(_ip: str) -> Optional[Dict[str, Any]]:
    """Default fetcher: a no-op that discovers nothing.

    Real discovery needs an operator-supplied transport/auth policy. The default
    deliberately performs no network call and holds no credentials, so running
    the CLI without wiring a fetcher is safe and inert.
    """
    return None


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    """Parse ``redfish-discover`` arguments."""
    parser = argparse.ArgumentParser(
        prog="redfish-discover",
        description=(
            "Read-only discovery of Redfish services on a list of hosts. "
            "Probes /redfish/v1/ and reports vendor, product, and Redfish "
            "version. Does not mutate any controller."
        ),
    )
    parser.add_argument(
        "hosts",
        nargs="*",
        help="Host addresses to probe (e.g. 10.0.0.10 10.0.0.11).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=32,
        help="Maximum number of concurrent probes (default: 32).",
    )
    return parser.parse_args(argv)


def redfish_discover_main(argv: Optional[Sequence[str]] = None) -> int:
    """Console entry point for ``redfish-discover``.

    :param argv: argument vector (defaults to ``sys.argv[1:]``).
    :return: process exit code. ``0`` always for a completed scan; ``2`` when no
        hosts were supplied (nothing to do).

    With the default fetcher the scan discovers nothing — wiring a real fetcher
    is an operator responsibility, kept out of this module so it never performs
    network I/O or touches credentials on its own.
    """
    args = _parse_args(argv)
    if not args.hosts:
        sys.stderr.write("redfish-discover: no hosts supplied; nothing to scan.\n")
        return 2

    services = asyncio.run(
        scan_subnet(args.hosts, _default_get, concurrency=args.concurrency)
    )
    render_table(services)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation only
    raise SystemExit(redfish_discover_main())
