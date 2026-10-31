#!/usr/bin/env python3
"""Connect horizon-ctl on this computer to Starling on a phone, through adb.

    python tools/phone_connect.py [--device SERIAL] [--out FILE]
    horizon-ctl --socket FILE state
    horizon-ctl --socket FILE mcp        # the MCP server, stdio

Needs a debug build (run-as reads the game's private endpoint file) with AI
Agent on, and the game running. The port changes with each launch: run this
again after one. The file holds the game's token, so it is written for this
user only.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PACKAGE = "io.github.juanluci.starling"
ENDPOINT = "files/horizon-control.json"


def remote_endpoint(raw: str) -> dict:
    """The phone's endpoint as this computer's client reads it."""
    endpoint = json.loads(raw)
    port, token = endpoint.get("port"), endpoint.get("token")
    if endpoint.get("transport") != "tcp" or not isinstance(port, int) or not token:
        raise ValueError("not a TCP control endpoint")
    return {"transport": "tcp", "port": port, "token": token, "remote": True}


def adb(device: str | None, *args: str) -> str:
    command = ["adb", *(["-s", device] if device else []), *args]
    done = subprocess.run(command, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip() or done.stdout.strip())
    return done.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", help="adb serial, when several are connected")
    parser.add_argument(
        "--out", type=Path, default=Path.home() / ".horizon-phone-control.json"
    )
    args = parser.parse_args()
    try:
        raw = adb(args.device, "exec-out", "run-as", PACKAGE, "cat", ENDPOINT)
        endpoint = remote_endpoint(raw)
        port = f"tcp:{endpoint['port']}"
        adb(args.device, "forward", port, port)
    except (RuntimeError, ValueError) as error:
        print(
            f"no control endpoint: {error}\n"
            "Is the game running, a debug build, with Horizon Settings > AI Agent on?",
            file=sys.stderr,
        )
        return 1
    descriptor = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as out:
        json.dump(endpoint, out)
    print(f"horizon-ctl --socket {args.out} state")
    return 0


def self_check() -> None:
    got = remote_endpoint('{"transport":"tcp","port":5,"token":"t"}')
    assert got == {"transport": "tcp", "port": 5, "token": "t", "remote": True}
    for bad in ('{"transport":"unix"}', '{"transport":"tcp","port":"5","token":"t"}'):
        try:
            remote_endpoint(bad)
        except ValueError:
            continue
        raise AssertionError(bad)


if __name__ == "__main__":
    self_check()
    sys.exit(main())
