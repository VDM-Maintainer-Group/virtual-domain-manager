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
    property string open_name: ""
    property string pred_name: ""
    property var domain_list: []

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
            highlight: root.open_name==root.pred_name
            anchors.centerIn: parent
        }
    }
}
