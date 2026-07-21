import argparse
import json
from pathlib import Path

from agent_core import schedule_from_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Schedule an interview with the mock agent")
    parser.add_argument("--input", help="Path to a JSON file containing the scheduling payload")
    args = parser.parse_args()

    if not args.input:
        parser.error("--input is required")

    payload_path = Path(args.input)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    result = schedule_from_payload(payload)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())