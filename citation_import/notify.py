"""macOS notification via osascript — no external dependencies required."""

import subprocess


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send(title: str, subtitle: str = "", body: str = "") -> None:
    parts = [f'display notification "{_escape(body)}"']
    parts.append(f'with title "{_escape(title)}"')
    if subtitle:
        parts.append(f'subtitle "{_escape(subtitle)}"')
    script = " ".join(parts)
    subprocess.run(["osascript", "-e", script], capture_output=True)
