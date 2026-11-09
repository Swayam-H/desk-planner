# Desk Planner

An interactive desktop wallpaper for a university student: a terminal/tmux-styled planner
(monthly/weekly calendar, today panel, to-dos, focus timer) that runs as a live web wallpaper
in **Lively Wallpaper** (Windows) or **Plash** (macOS).

## Files

- `desk-planner.html` — the whole app. One self-contained file: HTML, CSS and JS inline. No build step,
  no framework, no dependencies except the JetBrains Mono Google Font (falls back to Cascadia Mono / Consolas offline).

Keep it a single file: the wallpaper apps point at one local `.html` path.

## Hard constraints (it's a wallpaper)

- Must fit exactly one screen: `body` has `overflow:hidden`; only inner panes scroll.
  The user's laptop runs Windows at 1920×1080 with 125% scaling, i.e. a **1536×864 CSS viewport** — test there.
  Pane gaps (`--gap`) and the clock size scale with `vh` so shorter screens still fit.
- Screen margins for taskbar/dock/icons are user-set (`margins` dialog → CSS vars `--pt --pr --pb --pl`).
- Low CPU: redraws once per minute, aligned to the minute (`tick()`); the only per-second timer runs
  while a focus session is active. No animations except the blinking prompt cursor; respect
  `prefers-reduced-motion`.
- All data lives in `localStorage` under key `deskPlanner.v1`. Wrap storage in try/catch.
  Export/import JSON is the only backup — never break the data format without a migration in `normalize()`.
- Works fully offline. The only network use is optional **sync** to a private GitHub Gist (api.github.com, which allows
  CORS); every failure there must be silent apart from the `sync` button state. Links open with `openUrl()`
  (`window.open`, or `AndroidBridge.openUrl` in the app).
- In Lively, keyboard input must be enabled for the command line to work (this hides desktop icons),
  so every feature should also be reachable by clicking where practical.
- Lively keeps `localStorage` only with its **disk cache** setting on (`CefDiskCache`); otherwise every wallpaper load gets
  a fresh temp WebView2 profile and the planner starts over. Lively also cancels every download, so `doExport` (detected
  via `LIVELY`: `chrome.webview` and no `AndroidBridge`) just says so; a working sync counts as a backup in `updateBackup`.

## Layout

```
┌ 0:cal (72%) ─────────────────────────┐ ┌ 1:today (clock, date, fortune) ┐
│ ~/planner $ <command line>           │ │ 2:now   (now / next)          │
│ output line                          │ │ 3:schedule                     │
│ Month or Week view                   │ │ 4:todo  (+ quick-add input)    │
│                                      │ │ 5:due   (deadlines, 14 days)   │
└──────────────────────────────────────┘ │ 6:notes.txt                    │
┌ 7:progress ┐┌ 8:countdown ┐┌ 9:focus ┐ └────────────────────────────────┘
└────────────┘└─────────────┘└─────────┘
[desk] mood  timetable log help hide margins export import [backup]   now… bat focus clock
```

## Repo layout and the Android app

```
desk-planner.html              the app (wallpaper + phone layout), the one file to edit
android/                       WebView wrapper (Java, minSdk 29, AGP 8.2.2, Gradle 8.5)
  app/src/main/java/com/deskplanner/app/MainActivity.java
  app/debug.keystore           fixed signing key so updates install over old builds (keeps phone data)
.github/workflows/android.yml  on push to main: copies desk-planner.html to assets/index.html, builds the APK,
                               publishes it as a release (tag build-N) → /releases/latest/download/desk-planner.apk
```
The page is served from `https://appassets.androidplatform.net/assets/index.html` (WebViewAssetLoader) so it has a
real origin. `window.AndroidBridge` offers `saveFile(name,text)` (export → Downloads) and `openUrl(url)`; the
page defines `window.androidBack()` (close dialog → today tab → false lets the app go to background).
The Android SDK can't be downloaded in the cloud sandbox, so APKs are built by GitHub Actions only; Java can be
compile-checked locally against an android.jar from github.com/Reginer/aosp-android-jar.

## Sync (GitHub Gist)

`S.sync = {token, gist, etag, at, err}` is device-only and never exported. `save()` stamps `S.ft[field]` for every
synced field whose JSON changed (fields in `LOCAL_KEYS` don't sync: layout, mtab, private, fresh, fortunePick,
lastBackup, sync, ft, focusRun, view). `syncNow()` pulls (ETag), merges per field (newer `ft` wins), pushes if local
is newer; runs every 2 min, on wake, on `online`, and 4 s after an edit. `connectSync(token)` finds the gist by
description `desk-planner sync` or creates it; a joining device resets its `ft` so the synced data wins.
Test with a fake GitHub via Playwright `context.route('https://api.github.com/**', …)`.

## Phone layout (same file, `@media (max-width:760px)`)

The wallpaper layout is untouched above 760px. On phones: `.left/.side/.strip` become `display:contents`, so every
pane is one flex column ordered by its inline `--o`; each pane/row has `data-tabs` naming the bottom tabs it shows on
(today, cal, track, notes, more; `body[data-tab]`, saved as `S.mtab`, `setTab()`). The status bar becomes the "more"
menu; `.mrow` rows give touch buttons for things that otherwise need the command line; month cells show `.dots`
instead of event text; `#mchips` repeats the reminder and focus timer under the date. Test at 412×915 (`is_mobile`).

## Design language

- tmux-style panes: square 1px borders, title sitting on the top border (`.pane > .title`), numbered `n:name`.
- All copy lowercase, terminal voice (`# comment` for empty states, `[button]` for actions). No ALL-CAPS labels.
- Palette via CSS vars: `--bg --bar --line --dim --fg --cyan --red --green` set per theme in `THEMES`;
  `--amber` is the live accent, recalculated in `updateTheme()`:
  - theme `auto`: hue follows time of day (keyframes `KF`); other themes: fixed `acc`.
  - tinted toward red by deadlines today/tomorrow and to-dos due/overdue; toward green when all to-dos are done.
  - `--amber` / `--glow` are registered with `@property` so they fade.
- Late-night mode (01:00–05:00, `S.late`) dims via `body.late`. Privacy mode blurs every element with class `mk`.
  **Any new element showing personal text must get class `mk`.**
- Course colours: `S.colors` maps a lowercase course name → colour. `courseColor(title)` matches titles that
  equal/start with the name or contain `#name`.

## The user's timetable (Monsoon 2026, classes are 75-minute slots)

mon: AAD 08:30, DNA 11:40, DNA 17:10, feeding dogs 20:30 (30 min) · thu: AAD 08:30, DNA 11:40, ESW lab 14:00–17:00
tue/fri: OSN 10:05 · wed/sat: Prob & Stats 10:05, Science 1 11:40.
Attendance buttons only show for courses (a key in `S.colors` or `S.att`), not personal items.
Also the default in `sampleData()` and in `timetable.json`.

## Data model (`S`, saved as JSON)

```js
{
  timetable: [{ d: 0-6 (0=Sun), s:'HH:MM', e:'HH:MM', t:'course', r:'room' }],
  events:    { 'YYYY-MM-DD': [{ t, time:'HH:MM'|'', k:'event'|'deadline' }] },
  tasks:     [{ t, done, pri:0|1|2, due:'YYYY-MM-DD'|null, every:null|'day'|'week'|'w0'..'w6' }],
  countdowns:[{ t, date:'YYYY-MM-DD' }],
  sem:       { start, end } | null,
  focusLog:  { 'YYYY-MM-DD': minutes },  focusRun: { start:ms, len:min } | null,
  log:       { 'YYYY-MM-DD': [{ t, at:'HH:MM' }] },
  colors, links, notes, fortunes, fortunePick, fortuneOn,
  theme:'auto'|'amber'|'green'|'gruvbox'|'catppuccin'|'mono', view:'month'|'week',
  late, private, lastBackup, layout:{pt,pr,pb,pl},
  exams:     [{ c:'aad', date:'YYYY-MM-DD', time:'HH:MM'|'', topics:[{ t, done }] }],   // one exam per course key
  att:       { course: { p:attended, a:missed, l:approved leave } },  attMin: 75,
  attHist:   { course: [{ d:'YYYY-MM-DD', m:'p'|'a'|'l', at?:'HH:MM' }] },   // dated record; click A↔A/L in the dialog
  attMarks:  { 'YYYY-MM-DD|HH:MM|course': 'p'|'a' },  attLeave: 'skip'|'present',   // leave left out of total, or counted as attended
  focusBy:   { course: minutes },   // focus sessions tagged with a course (focusRun.tag)
  colorsSeeded: true                // PRESET_COLORS (aad osn dna prob science) applied once
}
```

`normalize()` fills defaults for older saves; add new fields there.
Tasks are kept sorted by `sortTasks()` (undone, priority, due) so displayed numbers = array index + 1.
Import: a backup `.json` **replaces** all data (after a confirm), but a `.json` without `tasks`/`events` (e.g. `{"timetable":[…]}`)
replaces only the fields it contains (`timetable.json`, `attendance.json` from the college portal); an `.ics` file **merges** its events
(`importIcs`, a week back to a year ahead, dedupes by date+time+title, "due/quiz/closes…" → deadline, "opens" → event).

Exams live in `S.exams`, not `S.events`; `dayEvents(key)` merges them in as pseudo-events `{t:'aad exam', k:'exam'}`
for the month/week views, the busy strip, today's schedule, 5:due and the urgency tint. `EXAM_LEN` = 180 min.
`courseKey(title)` gives the short course name (a colour key that matches, else the first word) used by
exams, attendance and focus tags.

## Code map (inside the `<script>`)

- helpers: `ymd fromYmd mins dur addDays mondayOf daysBetween isoWeek esc`
- calendar: `renderMonth` + `busyStrip` (08:00–20:00, half-hour cells), `renderWeek`, `renderCalendar`, `shift`, `goToday`, `setView`
- today column: `todayItems`, `renderSide`, `pickFortune`
- strip: `renderProgress`, `renderCountdowns` (pane 8:ahead, exams + countdowns), `renderFocus` (heatmap width fits the pane) + focus timer (`startFocus stopFocus finishFocus runFocusTicker`)
- exams: `findExam showExams renderExams` (dialog with clickable topic checklists)
- attendance: `attR attNums attPct attLine attAdvice attCell markAtt flipLeave histAdd histDrop` (✓ ✗ on started classes in 3:schedule) + `showAtt renderAtt` (attendance dialog, status-bar button, `att`)
- `focus add <min> [yday|date] [course]` logs a session by hand
- `S.fresh` is set by `sampleData()`; while true the output line suggests importing a backup (a new copy of the file in Lively gets empty storage)
- reminder: `renderSide` fills `#remind` in the status bar 10 min before the next item
- to-dos: `parseTask addTask toggleTask nextDue dueLabel renderTasks`
- command line: `run(line)` big switch; parsing `parseDate` (today/tom/weekday/`5 dec`/`5/12` d/m/ISO; returns
  `[null,n]` for impossible dates) and `parseTime`; help text in `HELP`
- theming: `applyTheme`, `updateTheme`, `updateLate`, `setPrivate`
- backup: `saveFile`, `doExport` (strips `S.sync`), `updateBackup` (nag after 7 days), import handler (keeps sync/layout)
- sync: `save takeSnap syncKeys packState mergeRemote pullGist pushGist syncNow syncSoon connectSync showSync renderSyncDlg`
- battery: `navigator.getBattery` (Chromium only; hidden on desktops / unsupported)
- entry: `renderAll()` then minute-aligned `tick()`

When adding a command: add a `case` in `run()`, a line in `HELP`, and keep messages short and lowercase.

## Testing

No test suite. Verify with headless Playwright (Python), faking the clock so time-based features are deterministic:

```python
ctx = browser.new_context(viewport={'width':1920,'height':1080}, timezone_id='Asia/Kolkata')
page = ctx.new_page()
page.clock.install(time='2026-11-02T12:10:00+05:30')
page.goto('file:///…/desk-planner.html')
page.fill('#cmd', 'add osn quiz fri 10am !'); page.press('#cmd', 'Enter')
print(page.inner_text('#out'))
page.screenshot(path='shot.png')
```

Collect `pageerror` events and check screenshots at 1920×1080. Quick syntax check:
`node -e "new Function(require('fs').readFileSync('desk-planner.html','utf8').split('<script>')[1].split('</script>')[0])"`

## Backlog (ideas not built yet)

- weekly review on Sundays (done tasks, focus hours, log highlights, next week's deadlines)
- vim-style navigation keys
- .ics: expand RRULE repeats (only the first date is imported now)
- android: class-reminder notifications (AlarmManager via the bridge), a home-screen widget
- sync: finer merges for lists (to-dos added on two devices between syncs: the later list wins today)
