from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import validate_index_location
from .documents import DocumentError, load_documents
from .index import rebuild_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Operações locais do Unnath Brain")
    parser.add_argument("command", choices=["validate", "rebuild"], help="operação a executar")
    args = parser.parse_args()
    brain_root = Path(os.getenv("BRAIN_ROOT", "brain"))
    db_path = Path(os.getenv("BRAIN_DB_PATH", "data/brain.db"))
    try:
        if args.command == "validate":
            count = len(load_documents(brain_root))
            print(f"Brain válido: {count} documento(s).")
        elif args.command == "rebuild":
            validate_index_location(brain_root, db_path)
            count = rebuild_index(brain_root, db_path)
            print(f"Índice reconstruído: {count} documento(s).")
    except (DocumentError, RuntimeError) as exc:
        parser.exit(1, f"Erro de validação: {exc}\n")


if __name__ == "__main__":
    main()
