"""
Command-Line Interface for the AdaptNXT Telemetry & Buffer Suite.
Allows immediate testing, database status inspection, and demonstration runs from the terminal.
Maintained by AdaptNXT Technology Solutions (https://www.adaptnxt.com).
"""

import argparse
import sys

from . import __version__
from .buffer_manager import SQLiteStoreAndForwardBuffer


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="adaptnxt-telemetry",
        description="AdaptNXT Industrial Modbus-to-MQTT Telemetry & Edge Buffer Utility"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Inspect local SQLite store-and-forward buffer status")
    status_parser.add_argument("--db", default="edge_telemetry_buffer.db", help="Path to SQLite buffer file")

    # Subcommand: demo
    subparsers.add_parser("demo", help="Run simulated CNC factory machine with store-and-forward failover")

    args = parser.parse_args()

    if args.command == "status":
        buf = SQLiteStoreAndForwardBuffer(db_path=args.db)
        pending = buf.get_pending_count()
        print(f"AdaptNXT Telemetry Buffer ({args.db}):")
        print(f" -> Total Pending Records: {pending}")
    elif args.command == "demo":
        from adaptnxt_telemetry.demo import run_demo
        run_demo()
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
