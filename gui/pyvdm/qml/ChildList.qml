import QtQuick 2.15

Rectangle {
    property var domain_model: null
    anchors.fill: parent
    color: "transparent"

    Component {
        id: listDelegate
        BasicElem {
            text: name
            highlight: selected
            has_shortcut: true
            anchors.horizontalCenter: parent.horizontalCenter

            width: parent.width * 0.80
            height: 50
            radius: 10

            function onDoubleClicked() { readOnly = false }

            Rectangle {
                property var bg_opacity: 0.50
                anchors.right: parent.right
                radius: parent.radius
                height: parent.height
                width: parent.width * 0.12
                //
                visible: show_shortcut
                color: "transparent"
                Rectangle {
                    anchors.fill: parent
                    color: "#FCFCF4"
                    opacity: parent.bg_opacity
                    radius: parent.radius
                }
                //
                Text {
                    anchors.centerIn: parent
                    color: "#FCFCF4"
                    text: shortcut
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
                    onEntered: { parent.bg_opacity = 0.70; parent.parent.propEnterEvent=true }
                    onExited:  { parent.bg_opacity = 0.50; parent.parent.propEnterEvent=false }
                    onPressed: { parent.bg_opacity = 0.80 }
                    onReleased: { parent.bg_opacity = 0.70 }
                    onClicked: {
                        console.log("clicked")
                    }
                }
            }
        }
    }

    ListView {
        anchors.centerIn: parent

        spacing: 20
        width: parent.width
        height: Math.min(parent.height, domain_model.count*50+(domain_model.count-1)*spacing)

        model: domain_model
        delegate: listDelegate
    }
}
