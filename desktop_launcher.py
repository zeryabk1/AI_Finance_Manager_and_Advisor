"""
Entry point for the packaged .exe.

What this does when double-clicked:
1. Boots Django using the bundled settings.
2. Runs `migrate` automatically (creates the database on first run,
   on the recipient's own machine, in %LOCALAPPDATA%\\AIFinanceManager).
   On the very first run (empty database) it also loads the demo company with
   6 months of sample data, so the app is never empty. Existing data is never touched.
3. Starts the Django dev server on 127.0.0.1:8000 in the background.
4. Opens the user's default browser to the app.
5. Keeps the process alive until it's stopped from Task Manager
   (there is no console window in this build).

This is intentionally simple (Django's built-in server, not a
production WSGI server) because it's meant for one person running
the app locally on their own PC - not for hosting it for others
over a network.

IMPORTANT: this file is built with PyInstaller's --windowed flag,
which means there is NO console attached. sys.stdout / sys.stderr
are None in that case, and a bare print() would crash the app.
Everything below is written to survive that: all output goes to a
log file instead.
"""
import os
import sys
import threading
import time
import webbrowser

# --- Where to put user data (same folder scheme as before) ---
APPDATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'AIFinanceManager')
os.makedirs(APPDATA_DIR, exist_ok=True)
LOG_PATH = os.path.join(APPDATA_DIR, 'app.log')

# --- Make print()/stdout/stderr safe with no console attached ---
# PyInstaller --windowed builds run with sys.stdout / sys.stderr set to
# None. Anything that tries to print() would raise AttributeError and
# silently kill the thread it's running on. Redirect both to a log file
# instead, so there's still somewhere to look if something goes wrong.
_log_file = open(LOG_PATH, 'a', buffering=1, encoding='utf-8')
if sys.stdout is None:
    sys.stdout = _log_file
if sys.stderr is None:
    sys.stderr = _log_file


def log(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{timestamp}] {message}'
    try:
        print(line)
    except Exception:
        pass


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financeproject.settings')

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402


def run_server():
    try:
        call_command('runserver', '127.0.0.1:8000', use_reloader=False, use_threading=True)
    except Exception as exc:
        log(f'Server thread crashed: {exc!r}')


def load_demo_data_if_empty():
    """First run only: if the database has no company yet, load the demo company + sample data.

    The seed command is imported and passed to call_command() as an object instead of by name,
    because management commands can't be discovered by name inside a PyInstaller bundle.
    A failure here must never stop the app from starting, so it is only logged.
    """
    try:
        from companies.models import Company
        if Company.objects.exists():
            return
        log('Empty database - loading demo data (first run only)...')
        from accounting.management.commands.seed_demo_data import Command as SeedDemoData
        call_command(SeedDemoData(), reset=False)
        log('Demo data loaded. Demo login -> username: demo / password: demo12345')
    except Exception as exc:
        log(f'Could not load demo data (app will still start): {exc!r}')


def show_error_dialog(title, message):
    """Best-effort native message box so a failure isn't totally silent
    when there's no console to read. Falls back to just logging."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        log(f'{title}: {message}')


def main():
    log('AI Finance Manager is starting...')
    log('Setting up the database (first run may take a few seconds)...')
    try:
        call_command('migrate', interactive=False, verbosity=1)
    except Exception as exc:
        log(f'Migration failed: {exc!r}')
        show_error_dialog(
            'AI Finance Manager - Startup Error',
            f'Could not set up the database:\n\n{exc}\n\nDetails were saved to:\n{LOG_PATH}',
        )
        return

    load_demo_data_if_empty()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(2)
    webbrowser.open('http://127.0.0.1:8000')

    log('AI Finance Manager is running at http://127.0.0.1:8000')
    log('It has no console window in this build - use Task Manager to stop it.')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
