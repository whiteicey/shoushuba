import os
from dataclasses import dataclass


@dataclass
class Config:
    base_url: str = ""
    username: str = ""
    password: str = ""
    entry_url: str = "http://soushu2030.com"

    @classmethod
    def load(cls, config_path: str = "config.txt") -> "Config":
        base_url = os.environ.get("SOUSHUBA_URL", "")
        username = os.environ.get("SOUSHUBA_USERNAME", "")
        password = os.environ.get("SOUSHUBA_PASSWORD", "")
        entry_url = os.environ.get("SOUSHUBA_ENTRY_URL", "http://soushu2030.com")

        if not base_url or not username or not password:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f.readlines()]
                if not base_url and len(lines) > 0:
                    base_url = lines[0]
                if not username and len(lines) > 1:
                    username = lines[1]
                if not password and len(lines) > 2:
                    password = lines[2]

        return cls(
            base_url=base_url.rstrip("/"),
            username=username,
            password=password,
            entry_url=entry_url.rstrip("/"),
        )

    def save_url(self, config_path: str = "config.txt") -> None:
        lines = []
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines()]

        if lines:
            lines[0] = self.base_url
        else:
            lines = [self.base_url, self.username, self.password]

        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @property
    def is_valid(self) -> bool:
        return bool(self.base_url and self.username and self.password != "userpassword")
