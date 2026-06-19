from __future__ import annotations

import argparse
import json

import uvicorn

from .api import app
from .schemas import BreachCheckRequest
from .service import BreachWatchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="breachwatch",
        description="Simulated dark web monitoring and breach intelligence backend.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check-email", help="Check a single email against the sample breach feed.")
    check_parser.add_argument("--email", required=True)
    check_parser.add_argument("--password")

    serve_parser = subparsers.add_parser("serve-api", help="Run the breachwatch FastAPI service.")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8010)

    subparsers.add_parser("dashboard", help="Print the current dashboard summary.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    service = BreachWatchService()

    if args.command == "check-email":
        result = service.check_email(BreachCheckRequest(email=args.email, password=args.password))
        print(json.dumps(result.model_dump(mode="json"), indent=2))
        return

    if args.command == "dashboard":
        print(json.dumps(service.dashboard_summary().model_dump(mode="json"), indent=2))
        return

    if args.command == "serve-api":
        uvicorn.run(app, host=args.host, port=args.port)
        return


if __name__ == "__main__":
    main()
