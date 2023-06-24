import QtQuick 2.15

Rectangle {
    property string open_name: ""
    property string pred_name: ""
    property var domain_model: null
    anchors.fill: parent
    color: "transparent"

    Component {
        id: listDelegate
        BasicElem {
            property var rect: parent? root_layout.mapFromItem(this, parent.x, parent.y, parent.width, parent.height) : Qt.rect(0,0,0,0)
            text: name
            highlight: selected
            always_show_shortcut: true
            shortcut_text: shortcut
            shortcut_width: parent? parent.width * 0.12 : 0
            shortcut_color: open_name.startsWith(name+'/')? highlightColor : defaultTextColor
            //
            width: parent? parent.width * 0.80 : 0
            height: 50
            radius: 10
            anchors.horizontalCenter: listDelegate.horizontalCenter
            //
            function onClicked(button) {
                text===symPLUS? controller.fork_domain(predName, true) : null
            }
            function onDoubleClicked(button) {
                if (button===Qt.RightButton) {
                    if (text) { readOnly = false }
                }
                else {
                    text!==symPLUS? controller.open_domain(text) : null
                }
            }
            function onShortcutClicked(button) {
                switch (shortcut_text) {
                    case symPLUS: controller.fork_domain(name, false); break;
                    case symNEXT: controller.set_pred_name(name); break;
                    case symDEL:  controller.delete_domain(name); break;
                    default: break;
                }
            }
            //FIXME: logic not correct
            // function onShortcutLongPress(button) {
            //     if (shortcut_text===symDEL) {
            //         shortcut_text = shortcut
            //         shortcut_color = open_name.startsWith(name+'/')? highlightColor : defaultTextColor
            //         shortcut_opacity = 0.40
            //     }
            //     else {
            //         shortcut_text = symDEL
            //         shortcut_color = "red"
            //         shortcut_opacity = 0.80
            //     }
            // }
        }
    }

    ListView {
        id: listView
        anchors.centerIn: parent

        spacing: 20
        width: parent.width
        height: Math.min(parent.height, domain_model.count*50+(domain_model.count-1)*spacing)

        model: domain_model
        delegate: listDelegate
    }
}
