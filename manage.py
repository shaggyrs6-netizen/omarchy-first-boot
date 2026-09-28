#!/usr/bin/env python3
"""Install/update scoped plugin files, verify, or remove without deleting history."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PLUGIN = 'shaggyrs6.first-boot'
CONFIG = Path.home() / '.config'
TARGET = CONFIG / 'omarchy/plugins' / PLUGIN
SHELL = CONFIG / 'omarchy/shell.json'
UNITS = CONFIG / 'systemd/user'
STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'first-boot'
FILES = ['bootlog.py', 'BarWidget.qml', 'manifest.json', 'manage.py', 'README.md']

def run(*cmd):
    return subprocess.run(cmd, check=True)

def save(path, text):
    tmp = path.with_suffix(path.suffix + '.first-boot-tmp')
    tmp.write_text(text)
    os.replace(tmp, path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'update', 'remove', 'verify'])
    parser.add_argument('--confirm-remove', action='store_true', help='Remove plugin files and its two units; preserve the boot log and backups')
    args = parser.parse_args()
    if args.action == 'verify':
        run('systemctl', '--user', 'is-enabled', 'first-boot.timer')
        run('systemctl', '--user', 'is-active', 'first-boot.timer')
        run('systemctl', '--user', 'start', 'first-boot.service')
        run('python3', str(TARGET / 'bootlog.py'), 'status')
        run('omarchy-shell', PLUGIN, 'status')
        print('reboot_verified is false until a different real boot has been recorded.')
        return
    if args.action == 'remove' and not args.confirm_remove:
        parser.error('Removal deletes only the five installed plugin files and first-boot.service/timer, and removes this bar entry. History and backups stay. Repeat with --confirm-remove to approve.')
    config = json.loads(SHELL.read_text())
    left = config['bar']['layout']['left']
    if args.action != 'remove' and not any('workspaces' in x.get('id', '') for x in left):
        raise SystemExit('No workspace widget found on the left; configuration unchanged.')
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = STATE / ('backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir()
    shutil.copy2(SHELL, backup / 'shell.json')
    if args.action == 'remove':
        run('systemctl', '--user', 'disable', '--now', 'first-boot.timer')
        run('systemctl', '--user', 'stop', 'first-boot.service')
        for section in config['bar']['layout'].values():
            section[:] = [x for x in section if x.get('id') != PLUGIN]
        save(SHELL, json.dumps(config, indent=2) + '\n')
        for filename in FILES:
            path = TARGET / filename
            if path.exists():
                shutil.copy2(path, backup / filename)
                path.unlink()
        for name in ['first-boot.service', 'first-boot.timer']:
            path = UNITS / name
            if path.exists():
                shutil.copy2(path, backup / name)
                path.unlink()
        # Leave any unrecognised files intact.
        if TARGET.exists() and not list(TARGET.iterdir()):
            TARGET.rmdir()
    else:
        source = Path(__file__).resolve().parent
        if args.action == 'install' and TARGET.exists():
            raise SystemExit('Already installed. Use update for a scoped, backed-up update.')
        TARGET.mkdir(parents=True, exist_ok=True)
        for filename in FILES:
            dest = TARGET / filename
            if dest.exists():
                shutil.copy2(dest, backup / filename)
            if source / filename != dest:
                save(dest, (source / filename).read_text())
        UNITS.mkdir(parents=True, exist_ok=True)
        service = '[Unit]\nDescription=Record PC boot times locally\n\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 "%h/.config/omarchy/plugins/shaggyrs6.first-boot/bootlog.py" collect\nUMask=0077\nTimeoutStartSec=120\n'
        timer = '[Unit]\nDescription=Keep the local PC boot ledger current\n\n[Timer]\nOnStartupSec=5\nOnUnitActiveSec=60\nAccuracySec=5\n\n[Install]\nWantedBy=default.target\n'
        for name, content in [('first-boot.service', service), ('first-boot.timer', timer)]:
            path = UNITS / name
            if path.exists():
                shutil.copy2(path, backup / name)
            save(path, content)
        run('systemctl', '--user', 'daemon-reload')
        run('systemctl', '--user', 'enable', '--now', 'first-boot.timer')
        run('systemctl', '--user', 'start', 'first-boot.service')
        for section in config['bar']['layout'].values():
            section[:] = [x for x in section if x.get('id') != PLUGIN]
        index = next(i for i, x in enumerate(left) if 'workspaces' in x.get('id', ''))
        left.insert(index + 1, {'id': PLUGIN})
        save(SHELL, json.dumps(config, indent=2) + '\n')
    run('systemctl', '--user', 'daemon-reload')
    run('omarchy-shell', 'shell', 'rescanPlugins')
    print('Done. Backups:', backup)

if __name__ == '__main__':
    main()
