from pathlib import Path


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".html",
    ".css",
    ".js",
    ".bat",
    ".sh",
    ".gitignore",
}


def convert(path):
    return Path(path).read_text(
        encoding="utf-8",
        errors="ignore",
    )