import QtQuick 2.0

Rectangle {
    property string text: ""
    property bool highlight: false
    //
    property color defaultColor:          "#5BA4FC"
    property color defaultHoveredColor:   "#5897EE"
    property color defaultPressedColor:   "#4F8AE2"
    //
    property color highlightColor:        "#FC3D39"
    property color highlightHoveredColor: "#E33437"
    property color highlightPressedColor: "#D42F32"

    color: highlight ? highlightColor : defaultColor

    Text {
        anchors.centerIn: parent
        color: "white"
        text: parent.text
        font.pixelSize: Math.min(parent.width/parent.text.length, 30)
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        //
        onEntered: {
            parent.color = parent.highlight ? parent.highlightHoveredColor : parent.defaultHoveredColor
        }
        onExited: {
            parent.color = parent.highlight ? parent.highlightColor : parent.defaultColor
        }
        onPressed: {
            parent.color = parent.highlight ? parent.highlightPressedColor : parent.defaultPressedColor
        }
        onReleased: {
            parent.color = parent.highlight ? parent.highlightHoveredColor : parent.defaultHoveredColor
        }
        //
        onClicked: if (typeof parent.onClicked === "function") {
            parent.onClicked(mouse.button)
        }
        onDoubleClicked: if (typeof parent.onDoubleClicked === "function") {
            parent.onDoubleClicked(mouse.button)
        }
    }
}
