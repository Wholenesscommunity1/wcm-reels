import csv, sys, re
from make_reels import *
import os
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "wcm_30_day_content_calendar.csv"), encoding="utf-8")))
OUT = os.environ.get("WCM_OUT", os.path.join(HERE, "reels"))
CASTL = ["maya", "marcus", "leah", "dev", "grace"]
ACC = {"Nutrition & Healing": CORAL, "Physical Wellness": TEAL, "Mind & Emotions": SAGE, "Stress Relief & Rest": SAGE,
       "Relationships & Support": CORAL, "Financial Wellness": SUN, "Spirituality & Purpose": SUN,
       "Conditions & Recovery": TEAL, "Home & Lifestyle": CORAL}
def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:28]
def scenes(r):
    i = int(r["Day"]); a = ACC[r["Dimension"]]; th = r["Theme"]
    who = CASTL[i % 5]; other = CASTL[(i + 2) % 5]
    pose, prop = "stand", None
    if th == "Recipe": pose, prop = "hold", ("bowl" if i % 2 else "pan")
    elif th == "Humor": pose, prop = "hold", "phone"
    elif th == "Good habit" and "water" in r["Hook"].lower(): pose, prop = "hold", "water"
    elif th in ("Encouragement", "Community"): pose = "wave"
    badge_txt = {"Recipe": "Easy recipe", "Workout": "Quick workout", "Good habit": "Good habit", "Humor": "Too real",
                 "Encouragement": r["Dimension"], "Community": "Community"}[th]
    lst = dict(kind="list", dur=5.2, accent=a, badge=r["Dimension"], title="Try this:", who=who,
               pose=("arms_up" if th == "Workout" else pose), prop=prop,
               items=[r["Line 1"], r["Line 2"], r["Line 3"], r["Line 4"]])
    return [
        dict(kind="hook", dur=2.8, accent=a, badge=badge_txt, who=who, pose=("flex" if th == "Workout" else pose), prop=prop, text=r["Hook"], sub=""),
        lst,
        dict(kind="punch", dur=2.8, accent=CORAL, text=r["Punchline"], sub="", who=who, pose="wave"),
        dict(kind="cta", dur=3.2, who=(who, other), text="Small steps. A brighter you."),
    ]
if __name__ == "__main__":
    for d in sys.argv[1:]:
        r = rows[int(d) - 1]
        print(render(f"day{int(d):02d}_{slug(r['Theme']+'_'+r['Dimension'])}", scenes(r), OUT), flush=True)
