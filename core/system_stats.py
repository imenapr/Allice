"""
ALLICE — System statistics helpers
"""

import sys
import subprocess


def get_disk_active_percent(letter: str) -> float | None:
    """
    Return disk active/busy time percentage for a drive letter (Windows).
    Matches Task Manager's '% Disk Time' / active time per logical drive.
    """
    if sys.platform != "win32":
        return None

    try:
        counter = rf"\LogicalDisk({letter}:)\% Disk Time"
        cmd = (
            f"(Get-Counter -Counter '{counter}' -ErrorAction Stop)"
            ".CounterSamples.CookedValue"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Windows locales may use comma as decimal separator
            raw = result.stdout.strip().replace(",", ".")
            return max(0.0, min(100.0, float(raw)))
    except Exception:
        pass
    return None
