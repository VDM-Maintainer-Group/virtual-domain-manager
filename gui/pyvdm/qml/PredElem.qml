import QtQuick 2.15

BasicElem {
    id: pred_elem
    property string name: ""
    text: name

    width: name === "" ? 25 : 50
    height: name === "" ? 25 : 50
    radius: width / 2
}
