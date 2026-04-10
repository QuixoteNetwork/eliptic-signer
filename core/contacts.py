from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class ContactsStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            self._save({})

    def _load(self) -> Dict[str, dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data: Dict[str, dict]) -> None:
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_contacts(self) -> Dict[str, dict]:
        return self._load()

    def add_contact(self, name: str, public_key_pem: str) -> None:
        data = self._load()
        data[name] = {"public_key_pem": public_key_pem}
        self._save(data)

    def remove_contact(self, name: str) -> None:
        data = self._load()
        target = name.strip().upper()
        for key in list(data.keys()):
            if key.strip().upper() == target:
                del data[key]
                break
        self._save(data)

    def get_public_key_pem(self, name: str) -> str | None:
        data = self._load()
        if name not in data:
            return None
        return data[name].get("public_key_pem")
    
    def rename_contact(self, old_name: str, new_name: str) -> None:
        data = self._load()

        old_target = old_name.strip().upper()
        new_target = new_name.strip().upper()

        if not new_target:
            raise ValueError("New contact name cannot be empty")

        old_key = None
        for key in data.keys():
            if key.strip().upper() == old_target:
                old_key = key
                break

        if old_key is None:
            raise KeyError(f"Contact not found: {old_name}")

        entry = data[old_key]
        del data[old_key]
        data[new_target] = entry
        self._save(data)
    
