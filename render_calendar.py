import csv, sys, re
from make_reels import *
from music import mood_for_row
import os
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "wcm_30_day_content_calendar.csv"), encoding="utf-8")))
OUT = os.environ.get("WCM_OUT", os.path.join(HERE, "reels"))
TAG = os.environ.get("WCM_TAG", "")            # e.g. WCM_TAG=v2 gives day07_..._v2.mp4 (new file name, so Metricool refetches)
CASTL = ["maya", "marcus", "leah", "dev", "grace"]
ACC = {"Nutrition & Healing": CORAL, "Physical Wellness": TEAL, "Mind & Emotions": VIOLET, "Stress Relief & Rest": SAGE,
       "Relationships & Support": PINK, "Financial Wellness": SUN, "Spirituality & Purpose": SKY,
       "Conditions & Recovery": TEAL, "Home & Lifestyle": CORAL}
SUB = {"Recipe": "Ingredients and steps below", "Workout": "No equipment. Go at your own pace.", "Good habit": "One small change this week",
       "Humor": "", "Encouragement": "", "Community": ""}
STICKER = {"Recipe": "Save this", "Workout": "Beginner friendly", "Good habit": "Try it today", "Humor": "Sound familiar?",
           "Encouragement": "You've got this", "Community": "Join us"}
def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:28]
def scenes(r):
    i = int(r["Day"]); a = ACC[r["Dimension"]]; th = r["Theme"]
    who = CASTL[i % 5]; other = CASTL[(i + 2) % 5]
    pose, prop, outfit = "stand", None, None
    if th == "Recipe": pose, prop = "hold", ("bowl" if i % 2 else "pan")
    if th == "Recipe" and i > 30:  # Middle Eastern recipe series with our kitchen host
        who = "layla"; h = r["Hook"].lower()
        prop = next((p for k, p in (("hummus", "hummus"), ("shakshuka", "shakshuka"), ("tabbouleh", "tabbouleh"), ("soup", "soup"),
                                    ("oats", "oats"), ("oatmeal", "oats"), ("chili", "soup"), ("curry", "soup"), ("shrimp", "pan"), ("cod", "pan"), ("fried rice", "bowl"), ("taco", "tacos"), ("stir fry", "pan"), ("sheet pan", "pan"), ("muffin", "pan"),
                                    ("sausage", "pan"), ("frittata", "pan"), ("tuna", "bowl"), ("salad", "bowl"),
                                    ("smoothie", "bowl"), ("noodle", "bowl"), ("patties", "pan"), ("salmon", "pan"),
                                    ("pancake", "bowl"), ("potato", "bowl"), ("bites", "bowl")) if k in h), prop)
    elif th == "Humor": pose, prop = "hold", "phone"
    elif th == "Good habit" and "water" in r["Hook"].lower(): pose, prop = "hold", "water"
    elif th in ("Encouragement", "Community"): pose = "wave"
    if th == "Workout": outfit = "tank"      # active wear on workout days
    badge_txt = {"Recipe": "Easy recipe", "Workout": "Quick workout", "Good habit": "Good habit", "Humor": "Too real",
                 "Encouragement": r["Dimension"], "Community": "Community"}[th]
    items = [r["Line 1"], r["Line 2"], r["Line 3"], r["Line 4"]]
    voiced = th == "Recipe"                  # the cook talks you through every recipe
    sub = SUB.get(th, "")
    if th == "Workout" and "jug" in r["Hook"].lower(): sub = "Just a water jug. Go at your own pace."
    if th == "Workout" and "towel" in r["Hook"].lower(): sub = "Just a bath towel. Go at your own pace."
    if th == "Workout" and "chair" in r["Hook"].lower(): sub = "Just a sturdy chair. Go at your own pace."
    hook = dict(kind="hook", dur=2.2, accent=a, badge=badge_txt, who=who, pose=("flex" if th == "Workout" else pose), prop=prop,
                outfit=outfit, text=r["Hook"], sub=sub, sticker=STICKER.get(th))
    lst = dict(kind="list", dur=4.4, accent=a, badge=r["Dimension"], title=("You need:" if th == "Recipe" else "Try this:"), who=who,
               pose=("arms_up" if th == "Workout" else pose), prop=prop, outfit=outfit, items=items)
    punch = dict(kind="punch", dur=2.0, accent=(CORAL if a != CORAL else TEAL), text=r["Punchline"], sub="", who=who, pose="wave", outfit=outfit,
                 sticker=("Save this" if th in ("Recipe", "Workout", "Good habit") else "Share this"))
    cta = dict(kind="cta", dur=2.8, who=(who, other), text="Small steps. A brighter you.", cta=r["CTA"] or None)
    if voiced:
        hook["vo"] = r["Hook"]; lst["vo_items"] = items; punch["vo"] = r["Punchline"]
        cta["vo"] = "Save this one. Then take the free Wholeness Assessment, link in bio."
    return [hook, lst, punch, cta]
def name_for(r):
    d = int(r["Day"]); return f"day{d:02d}_{slug(r['Theme']+'_'+r['Dimension'])}" + (f"_{TAG}" if TAG else "")
if __name__ == "__main__":
    for d in sys.argv[1:]:
        r = rows[int(d) - 1]
        print(render(name_for(r), scenes(r), OUT, mood_for_row(r["Theme"], r["Dimension"])), flush=True)
