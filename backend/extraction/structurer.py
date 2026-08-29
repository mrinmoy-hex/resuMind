import re
from pathlib import Path
from backend.storage.models import Resume


def build_resume(file_path: str, raw_text: str) -> Resume:
    candidate_name = _guess_name(raw_text, file_path)
    return Resume(
        file_path=file_path,
        candidate_name=candidate_name,
        raw_text=raw_text,
    )


def _guess_name(raw_text: str, file_path: str) -> str:
    for line in raw_text.splitlines():
        line = line.strip()
        if line and len(line.split()) <= 5 and not re.search(r"\d", line):
            return line
    return Path(file_path).stem