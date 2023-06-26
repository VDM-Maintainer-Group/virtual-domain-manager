import QtQuick 2.15

BasicElem {
    id: pred_elem
    property string name: symPLUS
    text: name
    shortcut_text: name&&name!==symPLUS? symBACK : ""
    shortcut_width: width
    shortcut_opacity: 0.8

    width: text ? 50 : 25
    height: text ? 50 : 25
    radius: width / 2

    function onDoubleClicked(button) {
        if (text===symPLUS) {
            controller.create_domain()
        }
    }

    function onShortcutClicked(button) {
        var _arr = name.split('/'); _arr.pop()
        var parent_name = _arr.join('/')
        predName = parent_name? parent_name : ""
        controller.set_pred_name(predName)
    }
}
