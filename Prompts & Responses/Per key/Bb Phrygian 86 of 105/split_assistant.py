#!/usr/bin/env python3
"""
Split a file into chunks by headers that look like:
  Assistant - <ALPHANUMERIC_ID>

Behavior:
- Starts at the first occurrence of 'Assistant - <ID>' anywhere in a line.
- Writes that line and following lines to a file named exactly 'Assistant - <ID>'.
- Switches to a new file when another header appears.
- By default, if the same ID appears later, content is appended to the same file.
  Use --overwrite to truncate the first time each file is opened in this run.

Tips:
- If your IDs contain underscores or hyphens, change the regex to [A-Za-z0-9_-]+.
"""

import os
import re
import sys
import argparse

# Accept common hyphen/dash variants: -, ‐, ‑, ‒, –, —
DASH_CHARS = r'-\u2010\u2011\u2012\u2013\u2014'
HEADER_RE = re.compile(
    rf'(?:\*\*)?\s*Assistant\s*[{DASH_CHARS}]\s*(?P<id>.+?)(?=\s*(?:\*\*)?\s*$)'
)

def split_by_assistant(input_path: str, output_dir: str, append: bool, verbose: bool, dry_run: bool) -> int:
    os.makedirs(output_dir, exist_ok=True)

    current_fh = None
    current_name = None
    seen_paths = set()
    headers_found = 0

    try:
        with open(input_path, "r", encoding="utf-8", errors="replace") as src:
            for lineno, line in enumerate(src, 1):
                m = HEADER_RE.search(line)
                if m:
                    headers_found += 1
                    assistant_id = m.group('id').strip()
                    out_name = f"Assistant - {assistant_id}"
                    out_path = os.path.join(output_dir, out_name)

                    # Close previous section
                    if current_fh:
                        current_fh.close()
                        current_fh = None

                    if verbose:
                        print(f"[match] line {lineno}: -> {out_name}", file=sys.stderr)

                    if not dry_run:
                        # Overwrite on first open if --overwrite, otherwise append
                        mode = "a"
                        if not append and out_path not in seen_paths:
                            mode = "w"
                        current_fh = open(out_path, mode, encoding="utf-8")
                        seen_paths.add(out_path)
                        current_name = out_name

                        # Write the header line to the new file
                        current_fh.write(line)
                else:
                    if current_fh and not dry_run:
                        current_fh.write(line)

    finally:
        if current_fh:
            current_fh.close()

    if verbose and headers_found == 0:
        print("No 'Assistant - <ID>' headers found. Check dash type/spaces/ID pattern.", file=sys.stderr)

    return 0 if headers_found > 0 else 2


def main():
    ap = argparse.ArgumentParser(description="Split file by 'Assistant - <ID>' sections.")
    ap.add_argument("input", help="Input text file")
    ap.add_argument("-o", "--output-dir", default=".", help="Output directory (default: current)")
    ap.add_argument("--overwrite", action="store_true",
                    help="Overwrite file the first time each ID is seen in this run (later occurrences append).")
    ap.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")
    ap.add_argument("-n", "--dry-run", action="store_true", help="Don't write files; just report matches")
    args = ap.parse_args()

    sys.exit(
        split_by_assistant(
            input_path=args.input,
            output_dir=args.output_dir,
            append=not args.overwrite,
            verbose=not args.quiet,
            dry_run=args.dry_run,
        )
    )

if __name__ == "__main__":
    main()
