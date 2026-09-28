import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
    id: root
    moduleName: "shaggyrs6.first-boot"
    property string label: "Loading boot log…"
    property string detail: "Reading the local boot log"
    readonly property string helper: decodeURIComponent(Qt.resolvedUrl("bootlog.py").toString().replace(/^file:\/\//, ""))
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    function refresh() { if (!reader.running) reader.running = true }
    function history() { Quickshell.execDetached(["ghostty", "-e", "python3", root.helper, "history"]) }
    Component.onCompleted: refresh()
    Timer { interval: 30000; running: true; repeat: true; onTriggered: root.refresh() }
    Process {
        id: reader
        command: ["python3", root.helper, "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var data = JSON.parse(text)
                    root.label = data.label
                    root.detail = data.tooltip
                } catch (e) {
                    root.label = "Boot log needs attention"
                    root.detail = "Could not read the local boot log. Run manage.py verify."
                }
            }
        }
        onExited: function(code) {
            if (code !== 0) {
                root.label = "Boot log needs attention"
                root.detail = "Could not read the local boot log. Run manage.py verify."
            }
        }
    }
    IpcHandler {
        target: "shaggyrs6.first-boot"
        function status(): string { return JSON.stringify({label: root.label, tooltip: root.detail}) }
        function refresh(): void { root.refresh() }
        function history(): void { root.history() }
    }
    WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: root.label
        fontSize: Style.font.body * 1.15
        tooltipText: root.detail
        onPressed: function(b) { if (b === Qt.LeftButton) root.history() }
    }
}
