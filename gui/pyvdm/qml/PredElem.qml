import QtQuick 2.15

BasicElem {
    id: pred_elem
    property string name: symPLUS
    text: name
    shortcut_text: name&&name!==symPLUS? symBACK : ""
    shortcut_width: width
    shortcut_opacity: 0.8

    width: name===symPLUS ? 25 : 50
    height: name===symPLUS ? 25 : 50
    radius: width / 2

    function onClicked(button) {
        if (name===symPLUS) {
            controller.create_domain()
        }
    }

    function onShortcutClicked(button) {
        var _arr = name.split('/'); _arr.pop()
        var parent_name = _arr.pop()
        predName = parent_name? parent_name : ""
        controller.set_pred_name(predName)
    }
}
