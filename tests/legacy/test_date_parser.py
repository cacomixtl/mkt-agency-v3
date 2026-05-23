from datetime import datetime
from app.api.v1.webhook import _parse_schedule_datetime

def test_parser():
    print("Testing parser...")
    
    # 1. Normal future date
    d1 = _parse_schedule_datetime("2026-05-10 10:00")
    print(f"Normal: {d1}")
    
    # 2. Year guessed wrong in the past (e.g. LLM says 2023 for March 10th)
    # The logic should roll it to 2026 or 2027 depending on if March is already past
    d2 = _parse_schedule_datetime("March 10, 2023 at 1:35 PM")
    print(f"Past year rolled forward: {d2}")
    
    # 3. Fuzzy LLM output
    d3 = _parse_schedule_datetime("Here is your schedule: 2026-10-15 14:00 (CST)")
    print(f"Fuzzy LLM output: {d3}")

if __name__ == "__main__":
    test_parser()
