# desk planner

A terminal-style planner: an interactive desktop wallpaper (Lively Wallpaper on Windows) and an Android app,
kept in sync through a private GitHub Gist.

- `desk-planner.html` is the whole planner. Point Lively at it on the laptop.
- Every push to `main` builds the Android app. On your phone, open this repo's **Releases** page
  (or `releases/latest/download/desk-planner.apk`) and install `desk-planner.apk`.
- To sync: in the planner open **sync**, paste a fine-grained GitHub token that only has *Gists: read and write*,
  and connect. Do the same on the other device.

See `CLAUDE.md` for how it's built.
