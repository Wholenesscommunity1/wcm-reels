# WCM Reels

Public hosting for Wholeness Community Marketplace Instagram reels (@wholenesscommunity), plus the scripts that build them.

- `reels/` finished 1080x1920 MP4s and JPG cover frames. Public URL pattern:
  `https://raw.githubusercontent.com/Wholenesscommunity1/wcm-reels/main/reels/<file>`
- `wcm_30_day_content_calendar.csv` the content plan (hooks, lines, captions, hashtags)
- `make_reels.py` renderer: characters, scene types, ffmpeg encode (needs Pillow + ffmpeg, Poppins font)
- `render_calendar.py` turns a calendar row into a reel: `python3 render_calendar.py 12` renders day 12
- `music.py` builds an original backing track for each reel (synthesized in code, no samples or licensed music). `make_reels.py` calls it on every render, so no reel goes out silent
- `calendar.py` generates the CSV from the content list inside it
- `schedule_plan.json` what was scheduled in Metricool and when

## Weekly workflow (automated)
1. Pull Metricool Instagram analytics for the last 14 days; note which reels got the most reach, plays, saves and shares.
2. Write 7 new calendar rows leaning toward the best-performing themes and dimensions; keep all nine dimensions in rotation over the month.
3. Render with `render_calendar.py` (reads the CSV in the repo root, writes to `reels/`, music included), commit and push to `main`. Check the result has sound: `ffmpeg -i reels/<file>.mp4 -af volumedetect -f null -` should report a mean volume near -16 dB, not -91 dB.
4. Schedule each in Metricool as an Instagram REEL at the best hour from `getBestTimeToPostByNetwork` (weekdays ~10:00 ET, recipes ~18:00 ET Tue/Thu, Sun ~12:00 ET).
5. Send a short summary to Sandip.

## Run log
- 2026-10-10: Every reel so far had a silent audio track. Added `music.py`, remuxed all 32 MP4s with music and updated the 30 queued Metricool reels (Oct 11 to Nov 9). Queue was already full through Nov 9, so no new rows were added. Two reels land at 18:00 on Oct 13, 22, 27 and Nov 3 (ours plus a stock-footage reel).
- 2026-10-11: Checked the queue for Oct 11 to Oct 25. Every day already has one of our reels (queue runs to Nov 9), so no new rows, renders or Metricool posts this run. All 36 MP4s in `reels/` measure about -16 dB mean volume, so none are silent. Days 31 to 34 (Nov 10, 12, 17, 19) are rendered but still not scheduled. The daily 18:00 stock-footage reels still overlap ours at 18:00 on Oct 13, 22, 27 and Nov 3. Analytics for Sep 27 to Oct 11 show only 4 published reels with single-digit reach, too little to steer themes yet.
- 2026-10-17: Analytics for Oct 3 to Oct 17 (8 of our reels published). Best of ours by reach: sheet pan salmon recipe (67 reach, 76 views), phone-free bedtime habit (24 reach, 35 views), berry bowl recipe (19 reach, 27 views). Humor reels trailed (2am brain 7 reach, Monday list 12 reach). Across the whole account the top reel was a stock-footage mindful eating clip (155 reach, 64 shares), so food and simple eating content is the clear lead; the next batch of rows should lean about 60 percent Recipe and Nutrition & Healing with concrete, numeric hooks. Every day from Oct 18 to Nov 9 already has one of our reels, so no new rows were written. Scheduled the four rendered Middle Eastern recipe reels (days 31 to 34) for Nov 10, 12, 17 and 19 at 18:00 ET. Moved our Oct 22, Oct 27 and Nov 3 recipe reels from 18:00 to 12:00 ET so they no longer post in the same minute as the daily 18:00 stock-footage reel (12:00 scores well in Metricool best-time data; 10:00 is the top hour every day). Next open days for new rows: Nov 11, 13, 14, 15, 16, 18, 20 onward.
- 2026-10-18: Analytics for Oct 4 to Oct 18 (9 of our reels published). Best of ours by reach: phone-free bedtime habit (106 reach, 123 views, 1 save), sheet pan salmon recipe (68 reach, 76 views), berry yogurt bowl recipe (19 reach, 27 views). Workouts sat in the middle (desk workout 18, commercial break 15), humor trailed again (texting a friend 16, Monday list 12, 2am brain 7). Account-wide, the stock mindful eating reel (155 reach, 64 shares) and fruit bowl (93 reach) still lead, so simple food and sleep habits with direct, concrete hooks are what works; "Me: / Also me:" humor does not. Every day from Oct 18 to Nov 9 already had one of our reels, so the next open days were used instead: wrote, rendered and scheduled days 35 to 41 for Nov 11, 13, 14, 15, 16, 18 and 20 (five Good habit rows, one budget Recipe, one Workout; dimensions Stress Relief & Rest, Financial, Physical, Relationships, Mind & Emotions, Home & Lifestyle, Conditions & Recovery; Nutrition already has four recipes on Nov 10, 12, 17, 19). All at 10:00 ET (top hour every weekday in best-time data), Sunday Nov 15 at 12:00. `render_calendar.py` now keeps the bowl or pan prop for a kitchen-host recipe whose hook names no Middle Eastern dish. Next open days: Nov 21, 22, 23 onward; Spirituality & Purpose is due next.
