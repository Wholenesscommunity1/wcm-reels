"""Build Instagram/Facebook captions (full recipe, under 2,200 characters) and calendar rows for recipe reels.

    python3 recipe_captions.py recipes/recipes_2026-11-11_to_11-24.json        # writes recipes/<date>/caption.txt and appends CSV rows
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "wholenesscommunitymarketplace.com"
CTAS = ["Take the free Wholeness Assessment", "Join the community free", "Find a provider on Wholeness Community"]
INTROS = {
    "Breakfast": "Breakfast that keeps you going until lunch.",
    "Lunch": "Lunch worth looking forward to.",
    "Dinner": "Dinner on the table without the stress.",
    "Snack": "A snack that works for you, not against you.",
    "Smoothie": "Five minutes, one blender, done.",
    "Dessert": "Dessert that fits a healthy week.",
}


def caption(r, cta):
    def body(step_text):
        lines = [r["hook"], "", r["benefit"] + ".", "",
                 f"{r['title']}", f"Serves {r['servings']}. Prep {r['prep']}, cook {r['cook']}.", "", "Ingredients:"]
        lines += [f"- {i}" for i in r["ingredients"]]
        lines += ["", "Steps:"]
        lines += [f"{k + 1}. {s}" for k, s in enumerate(step_text)]
        lines += ["", f"{cta} at {SITE} (link in bio).", "", r["hashtags"]]
        return "\n".join(lines)
    text = body(r["steps"])
    if len(text) > 2200:
        text = body(r.get("vo_steps") or r["steps"])   # shorter steps, every ingredient and amount stays
    assert len(text) <= 2200, (r["slug"], len(text))
    return text


def calendar_rows(recipes, start_day, captions):
    """Rows for wcm_30_day_content_calendar.csv with the existing columns plus Ingredients and Steps."""
    rows = []
    for k, (r, cap) in enumerate(zip(recipes, captions)):
        from datetime import date
        d = date.fromisoformat(r["date"])
        rows.append({
            "Day": str(start_day + k), "Date": r["date"], "Weekday": d.strftime("%a"), "Post time (ET)": "4:00 PM",
            "Dimension": "Nutrition & Healing", "Format": "Reel", "Theme": "Recipe", "Hook": r["hook"],
            "Line 1": r["steps"][0], "Line 2": r["steps"][1], "Line 3": r["steps"][2], "Line 4": r["steps"][3] if len(r["steps"]) > 3 else "",
            "Punchline": r["benefit"], "CTA": cap.split("\n")[-3].split(" at ")[0], "Website": SITE,
            "Stock video search terms": f"{r['title'].lower()} close up, person cooking {r['title'].lower()}, person enjoying {r['title'].lower()}",
            "AI video prompt (Veo / Kling / Runway)": r["cook_prompt"].replace("{person}", r["person"]),
            "Caption": cap, "Hashtags": r["hashtags"],
            "Ingredients": " | ".join(r["ingredients"]), "Steps": " | ".join(r["steps"]),
            "Title": r["title"], "Servings": r["servings"], "Prep": r["prep"], "Cook": r["cook"], "Cuisine": r["cuisine"], "Meal": r["meal"],
        })
    return rows


if __name__ == "__main__":
    recipes = json.load(open(sys.argv[1]))
    caps = []
    for k, r in enumerate(recipes):
        cap = caption(r, CTAS[k % 3])
        caps.append(cap)
        os.makedirs(os.path.join(HERE, "recipes", r["date"]), exist_ok=True)
        open(os.path.join(HERE, "recipes", r["date"], "caption.txt"), "w").write(cap)
        print(r["date"], len(cap))
    csv_path = os.path.join(HERE, "wcm_30_day_content_calendar.csv")
    existing = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    fields = list(existing[0].keys())
    for extra in ["Ingredients", "Steps", "Title", "Servings", "Prep", "Cook", "Cuisine", "Meal"]:
        if extra not in fields: fields.append(extra)
    start_day = max(int(e["Day"]) for e in existing) + 1
    have = {e["Hook"] for e in existing}
    new_rows = [row for row in calendar_rows(recipes, start_day, caps) if row["Hook"] not in have]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for e in existing: w.writerow({k: e.get(k, "") for k in fields})
        for row in new_rows: w.writerow({k: row.get(k, "") for k in fields})
    print("appended", len(new_rows), "rows starting at day", start_day)
