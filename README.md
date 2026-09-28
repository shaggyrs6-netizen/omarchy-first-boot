# First Boot

Shows **First boot 7:01 am** immediately after the workspace numbers on the bar. Hover for every boot today. Click to open the saved history in Ghostty; press Enter to close it.

The first time stays unchanged through subsequent reboots. A machine left running overnight shows **No boot today**. Suspend/wake and logging in again do not count as new boots. Times follow the machine's local timezone, including daylight saving changes. Boot time records when the PC started; it does not track other activities.

## Install, update, remove

From this folder:

```
python3 manage.py install
python3 manage.py update
python3 manage.py verify
python3 manage.py remove --confirm-remove
```

Install refuses an existing installation. Update changes only this plugin's five files, its two user service files, and its bar entry; backups are kept first. Remove deletes those same owned files and bar entry, preserving the log and backups. It leaves unrecognised files intact. Neither path restores an old full shell configuration over later customisations.

The installed manager is `~/.config/omarchy/plugins/shaggyrs6.first-boot/manage.py`. To update from a newer bundle, run the newer bundle's manager.

## Persistence and recovery

- Local SQLite ledger: `~/.local/state/first-boot/boots.sqlite3` (or `$XDG_STATE_HOME/first-boot`). One row per kernel boot ID, with atomic transactions and full synchronous commits. No network or added dependencies.
- The user's `first-boot.timer` starts at login and records every minute independently of the bar. The widget reads it every 30 seconds and visibly flags stale/failed reads.
- Current boot time comes from the kernel. Existing journal history is imported once per boot ID. Early journal timestamps are adjusted by their monotonic timestamp; if no early entry survives, the first available entry is explicitly marked approximate.
- The journal recovers boots that occurred without logging in, provided their records still exist and are readable. A boot never recorded locally and already removed from the journal cannot be recovered.
- History is retained; rows are tiny. No daily files to manage, no destructive automatic pruning. A broken ledger is left intact and produces a visible error rather than silently replacing history.
- PC clock accuracy governs boot-time accuracy. A later timezone change displays historical instants in the new local timezone.

## Actual reboot check

Before restarting, save your work normally. After the next reboot and login, allow up to one minute and run:

```
python3 ~/.config/omarchy/plugins/shaggyrs6.first-boot/manage.py verify
```

Check that `reboot_verified` is `true`, the bar still sits after the workspace numbers, and hovering lists the new boot while retaining today's first time. `true` means a different actual kernel boot ID has been persisted since installation; restarting the bar cannot satisfy it. A new calendar day correctly starts a new first time.

No restart is performed by this installer. A real reboot remains unverified until this check succeeds.
