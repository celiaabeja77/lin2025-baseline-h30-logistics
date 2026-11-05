"""Clone the author's repairer at the exact commit used for these results.

The author's repository has no license file, so its code is not redistributed here.
"""
import subprocess
from pathlib import Path

URL = "https://github.com/Songtuan-Lin/classical-domain-repairer.git"
COMMIT = "080e33b22d3adc2bbc60b50d888d2b74bd9d8494"
DEST = Path(__file__).resolve().parents[1] / "third_party" / "classical-domain-repairer"

if not DEST.exists():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", URL, str(DEST)], check=True)
subprocess.run(["git", "checkout", "--quiet", COMMIT], cwd=DEST, check=True)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=DEST, text=True).strip()
assert head == COMMIT, head
print(f"repairer ready at {DEST} ({head})")
