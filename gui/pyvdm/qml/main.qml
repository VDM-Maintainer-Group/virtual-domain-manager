import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import QtQuick.Layouts 1.10
// import QtQuick.Shapes 1.10

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
    ListModel { id: domain_model }

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
            domain_model.append({
                "name":list[i][0],
                "selected":list[i][1],
                "shortcut":list[i][2]
            })
        }
    }

    // Compnent Area
    RowLayout {
        focus: true
        anchors.fill: parent
        Keys.onEscapePressed: { root.close() }

        Rectangle {
            color: "transparent"
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: parent.width * 2/5
            Layout.preferredHeight: parent.height
            //
            PredElem {
                anchors.centerIn: parent
                name: root.pred_name
                highlight: root.open_name === root.pred_name
            }
        }

        Rectangle {
            color: "transparent"
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: parent.width * 3/5
            Layout.preferredHeight: parent.height
            visible: (domain_model.count>0)
            //
            ChildList {
                anchors.centerIn: parent
                domain_model: domain_model
            }
        }
    }
}
