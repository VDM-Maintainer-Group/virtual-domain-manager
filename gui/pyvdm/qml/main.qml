import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import QtQuick.Layouts 1.10

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
    property string openName: ""
    property string predName: ""
    ListModel {
        id: domain_model
        onDataChanged: canvas.requestPaint()
    }

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
        var length = Math.max(list.length, domain_model.count)
        for (var i = 0; i < length; i++) {
            list[i]? domain_model.set(i, list[i]) : domain_model.remove(i)
        }
    }

    // Component Area
    RowLayout {
        id: root_layout
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
                id: pred_elem
                anchors.centerIn: parent
                name: root.predName
                highlight: root.openName === root.predName
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
                id: child_list
                anchors.centerIn: parent
                open_name: root.openName
                pred_name: root.predName
                domain_model: domain_model
            }
        }
    }

    // Canvas Area
    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.lineWidth = 2
            ctx.strokeStyle = "#5BA4FC"
            ctx.clearRect(0, 0, width, height)
            //
            var start_x = pred_elem.x + pred_elem.width
            var start_y = pred_elem.y + pred_elem.height/2
            var list_view = child_list.children[0].contentItem.children
            for (var child in list_view) {
                if (!list_view[child].text) continue;
                var stop_x  = list_view[child].rect.x
                var stop_y  = list_view[child].rect.y + list_view[child].height/2
                //
                ctx.beginPath()
                ctx.moveTo(start_x, start_y)
                ctx.bezierCurveTo(start_x + 50, start_y, stop_x - 50, stop_y, stop_x, stop_y)
                ctx.stroke()
                ctx.closePath()
            }
        }
        //
        Timer {
            interval: 50
            running: true
            onTriggered: canvas.requestPaint()
        }
    }
}
