import QtQuick 2.0

ListView {
    property string open_name: ''
    property var domain_model: null
    
    height:parent.height
    spacing: 20

    model: domain_model
    delegate:
        BasicElem {
            highlight: selected
            text: name
            anchors.horizontalCenter: parent.horizontalCenter

            width: 200
            height: 50
            radius: 10
    }
}
