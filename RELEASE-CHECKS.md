# First Boot release checks

Reviewed 12 October 2026. This is a focused theme and packaging review, not a
security audit or a claim of marketplace approval.

## Theme behaviour

The source and installed BarWidget.qml matched at review time. The plugin uses
the native WidgetButton with `bar: root.bar`, does not set its own foreground
colour or font family, and sizes text using `Style.font.body * 1.15`.

The installed Omarchy WidgetButton implementation binds its foreground to
`bar.barForeground`, its font family to `bar.fontFamily`, and delegates tooltip
display to the host bar. Its fallbacks are the shared Color and Style values.
Consequently the plugin follows theme changes through native bindings rather
than a cached or hard-coded palette. No theme-specific code change was needed.

History launches Ghostty without palette overrides and prints plain text, so it
uses the user's terminal colours and font. Bar and terminal settings can differ.

This review checked the actual native component source and plugin bindings.
No live dark/light theme switch or exhaustive visual check of third-party bars
was performed. The tests guard the source contract; they are not rendered QML
theme tests. Vertical-bar layout is not certified.

## Release boundaries

- The thumbnail is an AI-generated illustration with fictional boot times.
- No personal boot ledger, desktop screenshot or user configuration is included.
- Existing source behaviour and installed desktop files were not changed.
- The installer needs manual setup and assumes the stock bar layout. Marketplace
  installation alone does not create the timer. Review this before submission.
- Removal through manage.py preserves the ledger and backups.
- Public source release and marketplace publication are separate steps.
