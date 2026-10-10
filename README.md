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
