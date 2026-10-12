# First Boot marketplace description

## Short description

Today's first PC boot on your bar, with today's reboots and a persistent local
history of past boots.

## Full description

First Boot answers a small question: when did I first turn the computer on today?

The bar keeps that first time visible even after later reboots. Hover to see
today's starts, or click to open a historical overview in Ghostty. Saved boots
are listed newest first with their date, local time, timezone and record source.
History stays on your computer and survives reboots.

The widget follows your Omarchy bar's colours and font. The history window uses
your Ghostty theme. There is no account, cloud service or API key.

It records actual PC boots, not logins, time spent working or waking from sleep.
A computer left running overnight shows “No boot today”. Earlier boots can be
imported from the readable system journal; approximate entries are labelled, and
boots missing from both the journal and the saved ledger cannot be recovered.

## Listing metadata

- Category: Widgets
- Tags: bar, system, quickshell
- Repository: https://github.com/shaggyrs6-netizen/omarchy-first-boot
- Plugin ID: shaggyrs6.first-boot
- Licence: MIT
- Preview: preview.png (illustration with sample data)
- Setup: manual; installer creates a systemd user timer and expects the stock
  bar layout. Custom-bar placement must be reviewed separately.

## Submission status

Prepared only. No marketplace issue has been submitted. Before submitting,
review the current marketplace form, installation behaviour and manual-setup
requirements, and obtain the owner's approval of the completed checklist.
