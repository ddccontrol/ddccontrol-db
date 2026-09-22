#!/usr/bin/env python3
"""Convert, validate and inspect candidate-v1 database files (no dependencies)."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent / "cbor"))
from codec import Invalid, MAX_FILE, diagnostic, encode
from model import convert, fallback_manifest, load


def atomic_write(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("convert", help="convert every XML file without flattening includes")
    cmd.add_argument("directory", type=Path)
    cmd.add_argument("output", type=Path)
    cmd.add_argument("--revision", help="database revision (default: options.xml date)")
    cmd.add_argument("--snapshot", type=Path, help="write deterministic source manifest sidecar")
    for name in ("validate", "dump", "rewrite"):
        cmd = sub.add_parser(name)
        cmd.add_argument("input", type=Path)
        if name == "rewrite":
            cmd.add_argument("output", type=Path)
            cmd.add_argument("--snapshot", type=Path, help="write guarded XML fallback sidecar")
    args = parser.parse_args()
    try:
        if args.command == "convert":
            try:
                database = convert(args.directory, args.revision)
                data = encode(database)
                if args.snapshot:
                    atomic_write(args.snapshot, encode(fallback_manifest(database)))
                atomic_write(args.output, data)
            except Exception:
                # Never let failed generation leave an older artifact beside
                # newer XML. The package build must fail, not reuse that file.
                args.output.unlink(missing_ok=True)
                if args.snapshot:
                    args.snapshot.unlink(missing_ok=True)
                raise
            print(f"{len(database[6])} profiles, {len(data)} bytes, snapshot {database[9].hex()}")
        else:
            with args.input.open("rb") as stream:
                database = load(stream.read(MAX_FILE + 1))
            if args.command == "dump":
                json.dump(diagnostic(database), sys.stdout, ensure_ascii=False, indent=2)
                print()
            elif args.command == "rewrite":
                # Preserve every unknown field and extension, including those
                # this version cannot execute. No lossy model projection.
                if args.snapshot:
                    atomic_write(args.snapshot, encode(fallback_manifest(database)))
                atomic_write(args.output, encode(database))
            else:
                print(f"valid candidate-v1: {len(database[6])} profiles, revision {database[2]}")
    except (Invalid, OSError, UnicodeError) as exc:
        print("cbor-db: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
