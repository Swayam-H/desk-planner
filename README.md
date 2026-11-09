# desk planner

A terminal-style planner: an interactive desktop wallpaper (Lively Wallpaper on Windows) and an Android app,
kept in sync through a private GitHub Gist.

- `desk-planner.html` is the whole planner. Point Lively at it on the laptop.
- Every push to `main` builds the Android app. On your phone, open this repo's **Releases** page
  (or `releases/latest/download/desk-planner.apk`) and install `desk-planner.apk`.
- To sync: in the planner open **sync**, paste a fine-grained GitHub token that only has *Gists: read and write*,
  and connect. Do the same on the other device.
- In Lively: turn on **disk cache** in Lively's settings (otherwise the planner forgets everything at each start), and
  save the token in a file named `sync-token.txt` next to `desk-planner.html` before adding the folder to Lively. Every
  copy Lively makes starts empty, and with that file it connects by itself and gets your data back.
  `sync-token.txt` is git-ignored; never commit it.

See `CLAUDE.md` for how it's built.
