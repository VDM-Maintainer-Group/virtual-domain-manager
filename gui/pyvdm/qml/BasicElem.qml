import QtQuick 2.15

Rectangle {
    readonly property string symNEXT: '→'
    readonly property string symBACK: '←'
    readonly property string symPLUS: '＋'
    readonly property string symDEL: '×'
    //
    property string text: ""
    property bool readOnly: true
    property bool highlight: false
    //
    property bool show_shortcut: false
    property bool always_show_shortcut: false
    property string shortcut_text: ""
    property var shortcut_radius: radius
    property var shortcut_width: 10
    property var shortcut_opacity : 0.40
    property color shortcut_color: "#FCFCF4"
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

    Connections {
        function onHighlightChanged() {
            color = highlight ? highlightColor : defaultColor
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
        text: parent.text.split('/').pop()
        font.pixelSize: Math.min(parent.width/text.length, 30)
        //
        onEditingFinished: {
            controller.update_name(parent.text, text_edit.text)
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

        //Shortcut Area
        Rectangle {
            id: shortcut_area
            anchors.right: parent.right
            radius: shortcut_radius
            height: parent.height
            width: shortcut_width
            //
            visible: shortcut_text && (always_show_shortcut || show_shortcut)
            color: "transparent"
            Rectangle {
                id: shortcut_bg
                anchors.fill: parent
                color: shortcut_color
                opacity: shortcut_opacity
                radius: shortcut_radius-1
            }
            //
            Text {
                anchors.centerIn: parent
                color: shortcut_opacity<0.75? "#FCFCF4" : "#BDC0BA"
                text: shortcut_text
                font.pixelSize: 25
                font.bold: true
            }
            //
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                preventStealing: true
                propagateComposedEvents: true
                //
                onEntered:  { shortcut_bg.opacity = shortcut_opacity + 0.1 }
                onExited:   { shortcut_bg.opacity = shortcut_opacity }
                onPressed:  { shortcut_bg.opacity = shortcut_opacity + 0.2 }
                onReleased: { shortcut_bg.opacity = shortcut_opacity + 0.1 }
                onClicked:  if (typeof parent.parent.parent.onShortcutClicked === "function") {
                    onShortcutClicked(mouse.button)
                }
                onDoubleClicked: if (typeof parent.parent.parent.onShortcutDoubleClicked === "function") {
                    onShortcutDoubleClicked(mouse.button)
                }
                onPressAndHold: if (typeof parent.parent.parent.onShortcutLongPress === "function") {
                    onShortcutLongPress(mouse.button)
                }
            }
        }
    }
}
