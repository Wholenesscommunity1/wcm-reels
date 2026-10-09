# WCM Reels

Public hosting for Wholeness Community Marketplace Instagram reels (@wholenesscommunity), plus the scripts that build them.

- `reels/` finished 1080x1920 MP4s and JPG cover frames. Public URL pattern:
  `https://raw.githubusercontent.com/Wholenesscommunity1/wcm-reels/main/reels/<file>`
- `wcm_30_day_content_calendar.csv` the content plan (hooks, lines, captions, hashtags)
- `make_reels.py` renderer: characters, scene types, ffmpeg encode (needs Pillow + ffmpeg, Poppins font)
- `render_calendar.py` turns a calendar row into a reel: `python3 render_calendar.py 12` renders day 12
- `calendar.py` generates the CSV from the content list inside it
- `schedule_plan.json` what was scheduled in Metricool and when

## Weekly workflow (automated)
1. Pull Metricool Instagram analytics for the last 14 days; note which reels got the most reach, plays, saves and shares.
2. Write 7 new calendar rows leaning toward the best-performing themes and dimensions; keep all nine dimensions in rotation over the month.
3. Render with `render_calendar.py`, commit and push to `main`.
4. Schedule each in Metricool as an Instagram REEL at the best hour from `getBestTimeToPostByNetwork` (weekdays ~10:00 ET, recipes ~18:00 ET Tue/Thu, Sun ~12:00 ET).
5. Send a short summary to Sandip.
