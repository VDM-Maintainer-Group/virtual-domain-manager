import QtQuick 2.15

Rectangle {
    property string text: ""
    property color defaultColor: "#5BA4FC"
    property color hoveredColor: "#5897EE"

    color: defaultColor

    Text {
        anchors.centerIn: parent
        text: parent.text
        color: "white"
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        //
        onEntered: {
            parent.color = parent.hoveredColor
        }
        onExited: {
            parent.color = parent.defaultColor
        }
        //
        onClicked: {
            console.log("button clicked")
        }
        onDoubleClicked: {
            console.log("button double clicked")
        }
    }
}
