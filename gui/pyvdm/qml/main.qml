import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Window 2.0
import QtQuick.Layouts 1.3
// import QtQuick.Shapes 2.0

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
    RowLayout {
        focus: true
        anchors.centerIn: parent
        spacing: 10

        Keys.onEscapePressed: { root.close() }

        Rectangle {
            color: "transparent"
            border.color: "black"
            border.width: 2
        }

        PredElem {
            name: root.pred_name
            highlight: root.open_name === root.pred_name
        }

        ChildList {
            open_name: root.open_name
            domain_list: root.domain_list
            visible: root.domain_list.length > 0
        }
    }
}
