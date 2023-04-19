import dataclasses
from pathlib import Path


@dataclasses.dataclass
class Config:
    template_name: str
    custom_report_headers: list
    amd_s2idle: Path = Path("~/bin/amd_s2idle.py").expanduser()

    def validate(self):
        if not (Path("templates") / self.template_name).is_dir():
            raise ValueError(f"Template directory not found: {self.template_name}")

    def __post_init__(self):
        self.validate()
