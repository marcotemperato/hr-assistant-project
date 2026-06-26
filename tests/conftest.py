import sys
from pathlib import Path

HR_ASSISTANT_DIR = Path(__file__).resolve().parents[1] / "hr_assistant"
sys.path.insert(0, str(HR_ASSISTANT_DIR))
