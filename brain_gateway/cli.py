from __future__ import annotations

import argparse

from .config import Settings
from .index import rebuild_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Operações locais do Unnath Brain")
    parser.add_argument("command", choices=["rebuild"], help="operação a executar")
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "rebuild":
        count = rebuild_index(settings.brain_root, settings.db_path)
        print(f"Índice reconstruído: {count} documento(s).")


if __name__ == "__main__":
    main()

