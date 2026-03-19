from __future__ import annotations

import os
import sys
from pathlib import Path

# 테스트가 프로젝트 루트에서 실행되도록 보정
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# 테스트/CI에서는 LLM 호출을 끄고 fallback 로직만 사용
os.environ.setdefault("MAFIA_USE_LLM", "0")

