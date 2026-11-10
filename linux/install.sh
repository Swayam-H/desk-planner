#!/usr/bin/env bash
# Sets up the desk planner wallpaper on Ubuntu / GNOME:
#   installs the few packages it needs, starts it at login, adds "Desk Planner" to the app menu, and starts it now.
# Run from the repo:  bash linux/install.sh          undo:  bash linux/install.sh --uninstall
# Extra options are passed to the launcher at login, e.g. bash linux/install.sh --monitor 1
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$DIR/desk-planner-wallpaper.py"
AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/desk-planner.desktop"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications/desk-planner.desktop"
DING="ding@rastersoft.com"   # ubuntu's desktop icons: an invisible full-screen window that sits over the planner and eats its clicks
DING_MARK="${XDG_DATA_HOME:-$HOME/.local/share}/desk-planner/ding-was-on"

if [[ "${1:-}" == "--uninstall" ]]; then
  pkill -f "$LAUNCHER" || true
  rm -f "$AUTOSTART" "$APPS"
  if [[ -f "$DING_MARK" ]]; then gnome-extensions enable "$DING" 2>/dev/null || true; rm -f "$DING_MARK"; fi
  echo "removed. your planner data stays in ~/.local/share/desk-planner (delete it to wipe it)."
  exit 0
fi

if ! /usr/bin/python3 -c "import gi; gi.require_version('Gtk','3.0'); gi.require_version('WebKit2','4.1')" 2>/dev/null; then
  echo "installing python3-gi, gir1.2-gtk-3.0 and gir1.2-webkit2-4.1 (asks for your password)…"
  sudo apt-get update -q
  sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
fi
chmod +x "$LAUNCHER"

# the planner covers the desktop icons anyway; turn them off so clicks reach it (uninstall turns them back on)
if command -v gnome-extensions >/dev/null && gnome-extensions info "$DING" 2>/dev/null | grep -qiE 'state: (enabled|active)'; then
  gnome-extensions disable "$DING" && mkdir -p "$(dirname "$DING_MARK")" && touch "$DING_MARK"
  echo "turned off ubuntu's desktop icons, which block clicks on the planner."
fi

EXEC="/usr/bin/python3 \"$LAUNCHER\"${*:+ $*}"
mkdir -p "$(dirname "$AUTOSTART")" "$(dirname "$APPS")"
cat > "$AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=Desk Planner wallpaper
Comment=Terminal-style planner as a live wallpaper
Exec=sh -c 'sleep 3; exec $EXEC'
Icon=x-office-calendar
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
cat > "$APPS" <<EOF
[Desktop Entry]
Type=Application
Name=Desk Planner
Comment=Start (or restart) the planner wallpaper
Exec=$EXEC --replace
Icon=x-office-calendar
Categories=Office;Calendar;
StartupWMClass=desk-planner
EOF

nohup /usr/bin/python3 "$LAUNCHER" --replace "$@" >/dev/null 2>&1 &
echo "done: the planner is on your desktop now and starts at every login."
echo "restart it any time from the app menu (Desk Planner). sync: open [sync] in the planner,"
echo "or put your token in $(dirname "$DIR")/sync-token.txt"
