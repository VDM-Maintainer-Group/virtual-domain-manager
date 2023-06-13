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

    // Background Area
    Rectangle {
        id: bg
        anchors.fill: parent
        color: "#FCFCF4"
        opacity: 0.90
        radius: 15
    }

    // Function Area
    function setDomainList(list) {
        domain_model.clear()
        for (var i = 0; i < list.length; i++) {
            domain_model.append({"name":list[i][0], "selected":list[i][1]})
        }
    }

    // Compnent Area
    ListModel { id: domain_model }

    RowLayout {
        focus: true
        anchors.fill: parent
        anchors.centerIn: parent
        width: parent.width
        height: parent.height

        Keys.onEscapePressed: { root.close() }

        PredElem {
            name: root.pred_name
            highlight: root.open_name === root.pred_name
            //
            Layout.alignment: Qt.AlignCenter
        }

        ChildList {
            open_name: root.open_name
            domain_model: domain_model
            visible: (domain_model.count>0)
            //
            Layout.alignment: Qt.AlignCenter
        }
    }
}
