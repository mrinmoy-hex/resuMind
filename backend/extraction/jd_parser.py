from backend.storage.models import JobDescription


def build_job_description(file_path: str, raw_text: str, title: str = "Untitled Role") -> JobDescription:
    return JobDescription(
        file_path=file_path,
        title=title,
        raw_text=raw_text,
    )