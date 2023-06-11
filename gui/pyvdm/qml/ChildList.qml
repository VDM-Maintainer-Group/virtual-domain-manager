import QtQuick 2.0

ListView {
    property string open_name: ''
    property var domain_list: []
    
    model: domain_list
    delegate:
        BasicElem {
            width: 200
            height: 50
            radius: 10
            highlight: parent.open_name===modelData[0]
            text:modelData[0]
        }
}
