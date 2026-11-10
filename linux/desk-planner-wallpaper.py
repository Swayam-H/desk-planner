#!/usr/bin/env python3
"""Desk planner as a live wallpaper on Ubuntu / GNOME (the Linux stand-in for Lively Wallpaper).

Opens desk-planner.html (the folder above this script) in a borderless WebKitGTK window that sits
under all other windows and fills the screen's free area (top bar and dock stay visible).

  python3 linux/desk-planner-wallpaper.py              # wallpaper (kept below every window)
  python3 linux/desk-planner-wallpaper.py --desktop    # true desktop layer, behind the desktop icons' layer
  python3 linux/desk-planner-wallpaper.py --window     # ordinary window, handy for trying it out
  python3 linux/desk-planner-wallpaper.py --monitor 1  # put it on another monitor
  python3 linux/desk-planner-wallpaper.py --replace    # restart: close the running one first

Needs: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1   (linux/install.sh does all of this)

- The page is served from http://127.0.0.1:47811 (only this folder's planner files), so it keeps one storage
  origin: data survives restarts, and a sync-token.txt next to desk-planner.html connects sync by itself.
- Storage lives in ~/.local/share/desk-planner. Exports go to ~/Downloads. Links open in the default browser.
- The page reloads by itself when desk-planner.html changes (after a git pull).
"""
import argparse
import http.server
import json
import os
import signal
import socketserver
import sys
import threading
import time

PORT = 47811
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, 'desk-planner.html')
SERVED = {'desk-planner.html', 'sync-token.txt', 'sync-token.txt.txt', 'timetable.json'}
DATA = os.path.join(os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share'), 'desk-planner')

ap = argparse.ArgumentParser(description='desk planner wallpaper for linux')
mode = ap.add_mutually_exclusive_group()
mode.add_argument('--desktop', action='store_true', help='use the desktop window layer (under desktop icons)')
mode.add_argument('--window', action='store_true', help='open as a normal window')
ap.add_argument('--replace', action='store_true', help='close a running planner wallpaper first')
ap.add_argument('--monitor', type=int, default=None, help='monitor number (default: primary)')
args = ap.parse_args()

# GNOME on Wayland lets no app place itself under other windows; through XWayland it can.
if os.environ.get('XDG_SESSION_TYPE') == 'wayland' and not args.window:
    os.environ['GDK_BACKEND'] = 'x11'

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    gi.require_version('WebKit2', '4.1')
    from gi.repository import Gdk, Gio, GLib, Gtk, WebKit2
except (ImportError, ValueError) as e:
    sys.exit(f'desk planner: missing packages ({e}).\n'
             'install them with: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1')


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves only the planner's own files, and only to 127.0.0.1:PORT (blocks DNS-rebinding pages)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        name = self.path.split('?', 1)[0].lstrip('/') or 'desk-planner.html'
        if self.headers.get('Host') != f'127.0.0.1:{PORT}' or name not in SERVED:
            return self.send_error(404)
        self.path = '/' + name
        super().do_GET()

    def do_HEAD(self):
        self.send_error(405)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


os.makedirs(DATA, exist_ok=True)
PIDFILE = os.path.join(DATA, 'wallpaper.pid')
if args.replace:
    try:
        with open(PIDFILE) as f:
            old = int(f.read().strip())
        with open(f'/proc/{old}/cmdline', 'rb') as f:
            if b'desk-planner-wallpaper' in f.read():
                os.kill(old, signal.SIGTERM)
    except (OSError, ValueError):
        pass
server = None
for _ in range(30):                                # the old one may need a moment to let go of the port
    try:
        server = Server(('127.0.0.1', PORT), Handler)
        break
    except OSError:
        if not args.replace:
            break
        time.sleep(0.2)
if not server:
    sys.exit(f'desk planner: port {PORT} is busy (already running? use --replace to restart it)')
with open(PIDFILE, 'w') as f:
    f.write(str(os.getpid()))
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/desk-planner.html'


def open_external(uri):
    try:
        Gio.AppInfo.launch_default_for_uri(uri, None)
    except GLib.Error as e:
        print('desk planner: could not open', uri, e.message, file=sys.stderr)


# persistent storage in one place, whatever the working directory
manager = WebKit2.WebsiteDataManager(base_data_directory=os.path.join(DATA, 'data'),
                                     base_cache_directory=os.path.join(DATA, 'cache'))
context = WebKit2.WebContext.new_with_website_data_manager(manager)
context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)

content = WebKit2.UserContentManager()
content.add_script(WebKit2.UserScript.new('window.deskPlannerLinux=true;',
                                          WebKit2.UserContentInjectedFrames.TOP_FRAME,
                                          WebKit2.UserScriptInjectionTime.START, None, None))
view = WebKit2.WebView(web_context=context, user_content_manager=content)
settings = view.get_settings()
settings.set_enable_developer_extras(True)        # right click → inspect element, for debugging
settings.set_javascript_can_open_windows_automatically(False)
settings.set_enable_write_console_messages_to_stdout(True)


def say(text, kind):
    """Show a line in the planner's output line (the page's own say())."""
    view.run_javascript(  # evaluate_javascript is newer than ubuntu 22.04's webkit
        f'try{{say({json.dumps(text)},{json.dumps(kind)})}}catch(e){{}}', None, None, None)


def on_policy(v, decision, kind):
    if kind == WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
        open_external(decision.get_navigation_action().get_request().get_uri())
        decision.ignore()
        return True
    if kind == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
        uri = decision.get_navigation_action().get_request().get_uri()
        if not uri.startswith((f'http://127.0.0.1:{PORT}/', 'blob:', 'data:', 'about:')):
            open_external(uri)
            decision.ignore()
            return True
    if kind == WebKit2.PolicyDecisionType.RESPONSE and not decision.is_mime_type_supported():
        decision.download()
        return True
    return False


def on_download(ctx, download):
    folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or os.path.expanduser('~')

    def decide(d, name):
        base, ext = os.path.splitext(os.path.basename(name) or 'planner-backup.json')
        path, n = os.path.join(folder, base + ext), 1
        while os.path.exists(path):
            path, n = os.path.join(folder, f'{base} ({n}){ext}'), n + 1
        d.set_allow_overwrite(False)
        d.set_destination(GLib.filename_to_uri(path, None))
        d.connect('finished', lambda *_: say('saved to ' + path.replace(os.path.expanduser('~'), '~', 1), 'ok'))
        return True

    download.connect('decide-destination', decide)
    download.connect('failed', lambda d, err: say('export failed: ' + err.message, 'err'))


view.connect('decide-policy', on_policy)
context.connect('download-started', on_download)
# the renderer can crash (out of memory, a GPU hiccup): bring the planner back instead of a blank wallpaper
view.connect('web-process-terminated', lambda *_: GLib.timeout_add_seconds(2, lambda: view.load_uri(URL) and False))

GLib.set_prgname('desk-planner')
win = Gtk.Window(title='desk planner')
win.add(view)
win.connect('destroy', Gtk.main_quit)
if not args.window:
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    win.stick()                                    # every workspace
    if args.desktop:
        win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
    else:
        win.set_keep_below(True)


def place(*_):
    """Fill the monitor's work area (the screen minus top bar and dock)."""
    display = Gdk.Display.get_default()
    mon = (display.get_monitor(args.monitor) if args.monitor is not None else None) \
        or display.get_primary_monitor() or display.get_monitor(0)
    area = mon.get_workarea() if not args.desktop else mon.get_geometry()
    if args.window:
        win.set_default_size(min(1536, area.width), min(864, area.height))
        return
    win.move(area.x, area.y)
    win.resize(area.width, area.height)
    win.set_size_request(area.width, area.height)


place()
screen = win.get_screen()
screen.connect('monitors-changed', place)
screen.connect('size-changed', place)

# reload when the planner file changes (git pull), checked every 30 s
mtime = [os.path.getmtime(PAGE)]


def check_page():
    try:
        m = os.path.getmtime(PAGE)
    except OSError:
        return True
    if m != mtime[0]:
        mtime[0] = m
        view.reload()
    return True


GLib.timeout_add_seconds(30, check_page)
# quit cleanly on logout / kill / ctrl+c, so WebKit writes the planner's storage to disk first
for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, sig, lambda *_: win.destroy() or False)
view.load_uri(URL)
win.show_all()
view.grab_focus()
try:
    Gtk.main()
except KeyboardInterrupt:
    pass
finally:
    server.shutdown()
