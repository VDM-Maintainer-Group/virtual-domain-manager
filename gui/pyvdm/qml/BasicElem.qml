import QtQuick 2.15

Rectangle {
    property string text: ""
    property bool readOnly: true
    property bool highlight: false
    property bool has_shortcut: false
    property bool show_shortcut: false
    //
    property color defaultColor:          "#5BA4FC"
    property color defaultHoveredColor:   "#5897EE"
    property color defaultPressedColor:   "#4F8AE2"
    //
    property color highlightColor:        "#FC3D39"
    property color highlightHoveredColor: "#E33437"
    property color highlightPressedColor: "#D42F32"
    //
    color: highlight ? highlightColor : defaultColor

    property bool propEnterEvent: false
    Connections {
        function onPropEnterEventChanged() {
            propEnterEvent? mouse_area.entered() : mouse_area.exited()
        }

        function onReadOnlyChanged() {
            if (!readOnly) {
                text_edit.cursorVisible = true
                text_edit.selectAll()
                text_edit.forceActiveFocus()
            }
        }
    }

    TextEdit {
        id: text_edit
        anchors.fill: parent
        readOnly: parent.readOnly
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        //
        color: "white"
        selectionColor: "#BDC0BA"
        text: parent.text
        font.pixelSize: Math.min(parent.width/parent.text.length, 30)
        //
        onEditingFinished: {
            parent.text = text_edit.text
            //TODO: back update
            parent.readOnly = true
            deselect()
        }
        Keys.onPressed: (event) => {
            if (!parent.readOnly) {
                if (event.key===Qt.Key_Return || event.key===Qt.Key_Enter || event.key===Qt.Key_Escape) {
                    event.accepted = true
                    editingFinished()
                }
            }
        }
    }

    MouseArea {
        id: mouse_area
        anchors.fill: parent
        hoverEnabled: true
        preventStealing: true
        propagateComposedEvents: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        //
        onEntered: {
            show_shortcut = true
            parent.color = parent.highlight ? parent.highlightHoveredColor : parent.defaultHoveredColor
        }
        onExited: {
            show_shortcut = false
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
