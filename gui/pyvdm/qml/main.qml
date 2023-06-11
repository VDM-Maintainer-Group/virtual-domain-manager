import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
// import QtQuick.Shapes 1.15

ApplicationWindow {
    id: root
    title: "PyVDM Traveral Diagram"
    visible: true
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"

    width: 720
    height: 405
    x: (Screen.width - width) / 2
    y: (Screen.height - height) / 2

    // Property Variable Area
    property string pred_name: "X1"
    property var domain_list: []
    property bool has_next_layer: false

    Rectangle {
        id: bg
        anchors.fill: parent
        color: "#FCFCF4"
        opacity: 0.90
        radius: 15
    }

    // Compnent Area
    Item {
        focus: true
        anchors.fill: parent
        Keys.onEscapePressed: { root.close() }

        PredElem {
            name: root.pred_name
            anchors.centerIn: parent
        }
    }
}
