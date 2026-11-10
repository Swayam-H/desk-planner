# desk planner

A terminal-style planner: an interactive desktop wallpaper (Lively Wallpaper on Windows, a small launcher on Ubuntu) and an Android app,
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

## On Ubuntu (GNOME)

```sh
git clone https://github.com/Swayam-H/desk-planner && cd desk-planner
bash linux/install.sh
```

That installs three small packages (`python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1`, asks for your password once),
puts the planner on your desktop under every window, and starts it at each login. It fills the screen between the top
bar and the dock, so the `margins` setting can stay at 0. Keyboard, mouse wheel, export (to `~/Downloads`) and links all work.

- Sync: open **sync** and paste your token, or save it as `sync-token.txt` next to `desk-planner.html` before the
  first start: the planner then connects by itself and pulls your data from the laptop/phone.
- Data stays in `~/.local/share/desk-planner` across restarts. `git pull` updates it; the page reloads by itself.
- Restart it from the app menu (**Desk Planner**). Other options: `python3 linux/desk-planner-wallpaper.py --help`
  (`--window` for a normal window, `--monitor 1`, `--desktop` for the desktop layer).
- The installer turns off Ubuntu's desktop icons (the `ding@rastersoft.com` extension): its invisible full-screen
  window sits over the planner and blocks every click. Uninstalling turns them back on.
- Remove it: `bash linux/install.sh --uninstall`.

See `CLAUDE.md` for how it's built.
