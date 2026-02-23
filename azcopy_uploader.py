import subprocess
import sys

# =====================================================
# CONFIG
# =====================================================
SOURCE = r"C:\Users\Louis-Martin Richard\PycharmProjects\OeilTest\output\bronze"

DEST = (
    "https://lawizlake.blob.core.windows.net/banquelaw"
    "?sp=racwdle"
    "&st=2026-02-23T01:05:12Z"
    "&se=2026-03-02T09:20:12Z"
    "&spr=https"
    "&sv=2024-11-04" 
    "&sr=c"
    "&sig=tn9LB%2FILapBJhVBVUYvTj0mo%2Fz8HISj%2F460AZIsdI78%3D"
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
    "--overwrite=ifSourceNewer",
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
