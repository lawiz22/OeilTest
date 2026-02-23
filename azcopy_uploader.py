import os
from pathlib import Path
import subprocess
import sys


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key and key not in os.environ:
            os.environ[key] = value

# =====================================================
# CONFIG
# =====================================================
SOURCE = r"C:\Users\Louis-Martin Richard\PycharmProjects\OeilTest\output\bronze"

_load_dotenv(Path(__file__).resolve().parent / ".env")

DEST = os.getenv("OEIL_AZCOPY_DEST", "")

if not DEST:
    print("❌ Missing OEIL_AZCOPY_DEST in .env (project root)")
    sys.exit(1)

# =====================================================
# AZCOPY COMMAND
# =====================================================
cmd = [
    "azcopy",
    "copy",
    SOURCE,
    DEST,
    "--recursive=true",
    "--output-type=text",
    "--from-to=LocalBlob",
    "--overwrite=ifSourceNewer",
    "--log-level=INFO"
]

print("🚀 Upload Bronze → ADLS (directory scoped)")
safe_dest = DEST.split("&sig=")[0] + "&sig=***" if "&sig=" in DEST else DEST
safe_cmd = cmd.copy()
safe_cmd[3] = safe_dest
print(" ".join(safe_cmd))

# =====================================================
# EXEC
# =====================================================
try:
    subprocess.run(cmd, check=True)
    print("✅ Upload terminé avec succès")
except subprocess.CalledProcessError as e:
    print("❌ Erreur AzCopy")
    sys.exit(e.returncode)
