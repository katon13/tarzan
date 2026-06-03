"""
Główny moduł uruchomieniowy TSP.

Przykłady:
    python -m core.TSP.tarzanTsp server
    python -m core.TSP.tarzanTsp client --host 127.0.0.1
    python -m core.TSP.tarzanTsp client --host 127.0.0.1 --smoke
"""

from __future__ import annotations

import argparse

from .tarzanTspConfig import TSP_BIND_HOST, TSP_MINI_PC_HOST, TSP_PORT
from .tarzanTspClient import run_interactive, run_smoke
from .tarzanTspServer import TarzanTspServer


def main() -> None:
    parser = argparse.ArgumentParser(description="TARZAN TSP")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_server = sub.add_parser("server", help="Uruchom TSP Server")
    p_server.add_argument("--host", default=TSP_BIND_HOST)
    p_server.add_argument("--port", type=int, default=TSP_PORT)
    p_server.add_argument("--node", default="tarzanMiniPC")
    p_server.add_argument("--lks", dest="lks", action="store_true", default=True, help="Włącz LKS na lokalnym TTY")
    p_server.add_argument("--no-lks", dest="lks", action="store_false", help="Wyłącz LKS")
    p_server.add_argument("--lks-tty", default="/dev/tty1", help="Ścieżka TTY dla LKS, np. /dev/tty1 albo -")
    p_server.add_argument("--lks-n5", dest="lks_n5", action="store_true", default=False, help="Włącz równoległe wyjście LKS-N5 / Nextion 5")
    p_server.add_argument("--lks-n5-port", default="", help="Port Nextion 5, najlepiej /dev/serial/by-id/...")
    p_server.add_argument("--lks-n5-baudrate", type=int, default=9600)
    p_server.add_argument("--lks-n5-dry-run", action="store_true", help="Test integracji LKS-N5 bez portu serial")
    p_server.add_argument("--lks-n5-refresh", type=float, default=2.0, help="Lekki interwał odświeżania LKS-N5 w sekundach")

    p_client = sub.add_parser("client", help="Uruchom TSP Client")
    p_client.add_argument("--host", default=TSP_MINI_PC_HOST)
    p_client.add_argument("--port", type=int, default=TSP_PORT)
    p_client.add_argument("--smoke", action="store_true")
    p_client.add_argument("--seconds", type=float, default=1.5)

    args = parser.parse_args()

    if args.mode == "server":
        server = TarzanTspServer(
            host=args.host,
            port=args.port,
            node_name=args.node,
            enable_lks=args.lks,
            lks_tty=args.lks_tty,
            enable_lks_n5=args.lks_n5,
            lks_n5_port=args.lks_n5_port,
            lks_n5_baudrate=args.lks_n5_baudrate,
            lks_n5_dry_run=args.lks_n5_dry_run,
            lks_n5_refresh_interval_s=args.lks_n5_refresh,
        )
        server.serve_forever()
    elif args.mode == "client":
        if args.smoke:
            raise SystemExit(run_smoke(args.host, args.port, args.seconds))
        run_interactive(args.host, args.port)


if __name__ == "__main__":
    main()
