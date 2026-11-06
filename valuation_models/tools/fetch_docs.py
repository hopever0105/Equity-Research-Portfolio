"""공시 원문 여러 건을 받아 <회사>/dart_docs/<rcept_no>.txt 로 저장하고 앞부분을 출력 (재사용용).
사용: python -m valuation.tools.fetch_docs 영원무역 20261027800219 20260811800871 ...
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from valuation.tools.dart import document_text

BASE = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    name, nos = sys.argv[1], sys.argv[2:]
    out = BASE / name / "dart_docs"
    n = int(__import__("os").environ.get("HEAD", "1500"))
    for no in nos:
        p = out / f"{no}.txt"
        t = p.read_text(encoding="utf-8") if p.exists() else document_text(no, out)
        t = re.sub(r"\.?xforms[^{}]*\{[^}]*\}", "", t, flags=re.I)
        t = re.sub(r"\n\s*\n+", "\n", t)
        if len(sys.argv) and __import__("os").environ.get("SKIP"):
            t = t[int(__import__("os").environ["SKIP"]):]
        print("=" * 20, no, len(t))
        print(t[:n])
        time.sleep(0.3)
