"""Compile .po catalogues to .mo without gettext (pure Python).

Django loads translations from compiled .mo files. `django-admin
compilemessages` needs the gettext tools (msgfmt), which are not available on
every machine, so this script writes the .mo binary format directly.

Usage: python scripts/compile_messages.py
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _unquote(text: str) -> str:
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return (
        text.replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\\\", "\\")
    )


def parse_po(path: Path) -> dict[str, str]:
    """Parse msgid/msgstr pairs (multi-line strings supported)."""
    entries: dict[str, str] = {}
    msgid: str | None = None
    msgstr = ""
    mode: str | None = None

    def flush():
        if msgid is not None:
            entries[msgid] = msgstr

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            flush()
            msgid = _unquote(line[len("msgid "):])
            msgstr = ""
            mode = "id"
        elif line.startswith("msgstr "):
            msgstr = _unquote(line[len("msgstr "):])
            mode = "str"
        elif line.startswith('"'):
            if mode == "id":
                msgid = (msgid or "") + _unquote(line)
            elif mode == "str":
                msgstr += _unquote(line)

    flush()
    return entries


def write_mo(entries: dict[str, str], path: Path) -> None:
    """Write the GNU .mo binary format (little-endian, no hash table).

    Layout: header, key table, value table, then all key strings followed by
    all value strings. Offsets are relative to the start of the file.
    """
    keys = sorted(entries)
    key_table_offset = 7 * 4
    value_table_offset = key_table_offset + len(keys) * 8
    data_offset = value_table_offset + len(keys) * 8

    ids = b""
    strs = b""
    key_positions = []
    value_positions = []
    for key in keys:
        key_bytes = key.encode("utf-8")
        value_bytes = entries[key].encode("utf-8")
        key_positions.append((len(key_bytes), len(ids)))
        value_positions.append((len(value_bytes), len(strs)))
        ids += key_bytes + b"\x00"
        strs += value_bytes + b"\x00"

    total_ids = len(ids)

    output = struct.pack(
        "Iiiiiii",
        0x950412DE,  # magic
        0,  # format revision
        len(keys),
        key_table_offset,
        value_table_offset,
        0,  # hash table size
        0,  # hash table offset
    )
    for key_len, key_pos in key_positions:
        output += struct.pack("ii", key_len, data_offset + key_pos)
    for value_len, value_pos in value_positions:
        output += struct.pack("ii", value_len, data_offset + total_ids + value_pos)
    output += ids + strs

    path.write_bytes(output)


def main() -> int:
    compiled = 0
    for po_path in sorted(ROOT.glob("locale/*/LC_MESSAGES/*.po")):
        mo_path = po_path.with_suffix(".mo")
        entries = parse_po(po_path)
        write_mo(entries, mo_path)
        print(
            f"compiled {po_path.relative_to(ROOT)} -> "
            f"{mo_path.relative_to(ROOT)} ({len(entries)} strings)"
        )
        compiled += 1

    if compiled == 0:
        print("no .po files found")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
