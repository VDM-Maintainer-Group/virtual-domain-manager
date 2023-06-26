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
            property var back_sc: null
            property var rect: parent? root_layout.mapFromItem(this, parent.x, parent.y, parent.width, parent.height) : Qt.rect(0,0,0,0)
            text: name
            highlight: selected
            always_show_shortcut: true
            shortcut_text: shortcut
            shortcut_width: parent? parent.width * 0.12 : 0
            shortcut_color: {
                if (shortcut===symDEL) {
                    return "red"
                }
                else {
                    return open_name.startsWith(name+'/')? highlightColor : defaultTextColor
                }
            }
            shortcut_opacity: shortcut===symDEL? 0.80 : 0.40
            //
            width: parent? parent.width * 0.80 : 0
            height: 50
            radius: 10
            anchors.horizontalCenter: listDelegate.horizontalCenter
            //
            function onDoubleClicked(button) {
                if (button===Qt.RightButton) {
                    if (text && shortcut==symPLUS) { readOnly = false }
                }
                else {
                    text===symPLUS? controller.fork_domain(predName, true) : controller.open_domain(text)
                }
            }
            function onShortcutClicked(button) {
                switch (shortcut_text) {
                    case symNEXT: controller.set_pred_name(name); break;
                    case symDEL:  controller.delete_domain(name); break;
                    default: break;
                }
            }
            function onShortcutDoubleClicked(button) {
                switch (shortcut_text) {
                    case symPLUS: controller.fork_domain(name, false); break;
                    default: break;
                }
            }
            //FIXME: logic not correct
            function onShortcutLongPress(button) {
                if (shortcut===symDEL) {
                    shortcut = back_sc.text
                }
                else if (shortcut===symPLUS) {
                    back_sc = {"text":shortcut}
                    shortcut = symDEL
                }
            }
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
