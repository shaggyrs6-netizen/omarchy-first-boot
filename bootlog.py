#!/usr/bin/env python3
"""Local boot ledger. Standard library only; SQLite commits survive interruptions."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'first-boot'

def current_boot():
    identity = Path('/proc/sys/kernel/random/boot_id').read_text().strip().replace('-', '')
    epoch = next(int(line.split()[1]) for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime '))
    return identity, epoch

def connect():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(STATE / 'boots.sqlite3', timeout=20)
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS boots (id TEXT PRIMARY KEY, epoch REAL NOT NULL, source TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)')
    return db

def collect(db):
    identity, epoch = current_boot()
    with db:
        db.execute('INSERT OR IGNORE INTO boots VALUES (?, ?, ?)', (identity, epoch, 'kernel boot time'))
    warning = ''
    try:
        result = subprocess.run(['journalctl', '--list-boots', '--no-pager', '-o', 'json'], capture_output=True, text=True, timeout=20, check=True)
        boots = json.loads(result.stdout)
        for boot in boots:
            if db.execute('SELECT 1 FROM boots WHERE id=?', (boot['boot_id'],)).fetchone():
                continue
            first = int(boot['first_entry']) / 1e6
            source = 'journal first entry (approximate)'
            epoch = first
            try:
                result = subprocess.run(['journalctl', '-b', boot['boot_id'], '--since', '@%.6f' % first, '--until', '@%.6f' % (first + 0.1), '-o', 'json', '--no-pager', '--output-fields=__REALTIME_TIMESTAMP,__MONOTONIC_TIMESTAMP'], capture_output=True, text=True, timeout=5, check=True)
                entry = json.loads(result.stdout.splitlines()[0])
                mono = int(entry['__MONOTONIC_TIMESTAMP']) / 1e6
                # Only infer start from an early entry: later entries may follow suspend.
                if 0 <= mono < 120:
                    epoch = int(entry['__REALTIME_TIMESTAMP']) / 1e6 - mono
                    source = 'journal boot time'
            except (ValueError, KeyError, IndexError, subprocess.SubprocessError):
                pass
            with db:
                db.execute('INSERT OR IGNORE INTO boots VALUES (?, ?, ?)', (boot['boot_id'], epoch, source))
    except (ValueError, KeyError, subprocess.SubprocessError) as exc:
        warning = 'Journal unavailable; current boot and saved history retained.'
    with db:
        db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('last_collection', str(time.time())))
        db.execute('INSERT OR REPLACE INTO meta VALUES (?, ?)', ('warning', warning))
        db.execute('INSERT OR IGNORE INTO meta VALUES (?, ?)', ('installed_boot', identity))
    return warning

def display(rows, now=None):
    now = now or dt.datetime.now().astimezone()
    today = [(i, dt.datetime.fromtimestamp(e).astimezone(), s) for i, e, s in rows if dt.datetime.fromtimestamp(e).astimezone().date() == now.date()]
    today.sort(key=lambda r: r[1].timestamp())
    def clock(value):
        return value.strftime('%I:%M %p').lstrip('0').lower()
    label = 'First boot ' + clock(today[0][1]) if today else 'No boot today'
    if today and 'approximate' in today[0][2]:
        label = label.replace('First boot ', 'First boot ~')
    lines = ['Boots today — ' + now.strftime('%a %d %b'), '']
    for n, (_, date, source) in enumerate(today):
        lines.append(('First: ' if n == 0 else 'Reboot: ') + clock(date) + (' (approx.)' if 'approximate' in source else ''))
    if not today:
        lines.append('No boot recorded today. The PC may have stayed on overnight.')
    lines.extend(['', 'Click for saved history.'])
    return {'label': label, 'tooltip': '\n'.join(lines), 'today_count': len(today)}

def status(db):
    rows = db.execute('SELECT id, epoch, source FROM boots ORDER BY epoch').fetchall()
    result = display(rows)
    meta = dict(db.execute('SELECT key, value FROM meta'))
    if time.time() - float(meta.get('last_collection', '0')) > 180:
        result['label'] = 'Boot log needs attention'
        result['tooltip'] = 'The boot recorder has not refreshed recently.\nRun manage.py verify.'
    elif meta.get('warning'):
        result['tooltip'] += '\n' + meta['warning']
    result['reboot_verified'] = current_boot()[0] != meta.get('installed_boot', current_boot()[0]) and any(r[0] == current_boot()[0] for r in rows)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['collect', 'status', 'history'])
    args = parser.parse_args()
    os.umask(0o077)
    with connect() as db:
        if args.action == 'collect':
            collect(db)
        elif args.action == 'history':
            print('PC BOOT HISTORY — local times\n')
            print(status(db)['tooltip'].replace('Click for saved history.', ''))
            print('\nSaved boots (newest first):\n')
            for identity, epoch, source in db.execute('SELECT id, epoch, source FROM boots ORDER BY epoch DESC'):
                print(dt.datetime.fromtimestamp(epoch).astimezone().strftime('%a %d %b %Y  %I:%M:%S %p %Z'), ' — ', source)
            print('\nOnly PC boot times are recorded.\n')
            if sys.stdin.isatty():
                input('Press Enter to close.')
        else:
            print(json.dumps(status(db)))

if __name__ == '__main__':
    main()
