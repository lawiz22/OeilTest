import subprocess
import sys

# =====================================================
# CONFIG
# =====================================================
SOURCE = r"C:\Users\Louis-Martin Richard\PycharmProjects\OeilTest\output\bronze"

DEST = (
    "https://lawizlake.blob.core.windows.net/banquelaw"
    "?sp=racwdl"
    "&st=2026-02-15T13:47:00Z"
    "&se=2026-02-15T22:02:00Z"
    "&spr=https"
    "&sv=2024-11-04"
    "&sr=c"
    "&sig=1pyNQMOzXazpqEh3BvYmJ%2FGwkBqWyxh4ppb3zDdhVRI%3D"
)

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
    "--overwrite=true",
    "--log-level=INFO"
]

print("🚀 Upload Bronze → ADLS (directory scoped)")
print(" ".join(cmd))

# =====================================================
# EXEC
# =====================================================
try:
    subprocess.run(cmd, check=True)
    print("✅ Upload terminé avec succès")
except subprocess.CalledProcessError as e:
    print("❌ Erreur AzCopy")
    sys.exit(e.returncode)
