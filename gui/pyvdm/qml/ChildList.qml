import QtQuick 2.0

ListView {
    property string open_name: ''
    property var domain_model: null
    
    spacing: 20
    width: parent.width
    height: Math.min(parent.height, domain_model.count*50+(domain_model.count-1)*spacing)

    model: domain_model
    delegate:
        BasicElem {
            text: name
            highlight: selected
            anchors.horizontalCenter: parent.horizontalCenter

            width: parent.width * 0.8
            height: 50
            radius: 10
    }
}
