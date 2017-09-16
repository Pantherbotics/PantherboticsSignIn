function createRow(studentID) {
    $.getJSON("/api/getinfo?id=" + studentID, _createRowCallback)
}

function zeroPad(str) {
    return ("00" + str).slice(-2)
}

function numberToTime(number) {
    var sec_num = parseInt(number, 10); // don't forget the second param
    var hours = Math.floor(sec_num / 3600);
    var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
    var seconds = sec_num - (hours * 3600) - (minutes * 60);

    if (hours < 10) { hours = "0" + hours; }
    if (minutes < 10) { minutes = "0" + minutes; }
    if (seconds < 10) { seconds = "0" + seconds; }
    return hours + ':' + minutes + ':' + seconds;
}

function _createRowCallback(data) {
    updateTop = false
    studentID = data['id']
    if (data['lastSession'] == null) {
        lastDate = "---"
        lastDuration = "---"
    } else {
        startDate = new Date(data['lastSession']['start_time'])
        endDate = new Date(data['lastSession']['end_time'])
        lastDate = (startDate.getMonth() + 1) + "/" + startDate.getDate() + "/" + startDate.getFullYear()
        lastDuration = numberToTime(data['lastSession']['duration'])
    }

    if (data['state'] == null) {
        state = "---"
        currentDuration = "---"
        color = ""
    } else {
        scanDate = new Date(data['state']['timestamp'])
        state = data['state']['status']
        if (state == 'scanin') {
            currentDuration = "---"
            setInterval(updateRowClock, 1000, studentID, scanDate)
            color = "table-success"
            updateTop = true
        } else if (state == 'timeout') {
            color = "table-warning"
            currentDuration = "---"
            updateTop = true
        } else {
            currentDuration = "---"
            color = "table-selected"

        }
    }

    r = "<tr id='" + studentID + "-row' class='" + color + "'>"
    r = r + "<td id='" + studentID + "-name'></td>"
    r = r + "<td id='" + studentID + "-id'></td>"
    r = r + "<td id='" + studentID + "-state'></td>"
    r = r + "<td id='" + studentID + "-clength'></td>"
    r = r + "<td id='" + studentID + "-plength'></td>"
    r = r + "<td id='" + studentID + "-pdate'></td>"
    r = $(r + "</tr>")

    if (updateTop) {
        $('#status-table-header').after(r)
    } else {
        $('#status-table > tbody:last-child').append(r)
    }

    $("#" + studentID + "-name").text(data['name'])
    $("#" + studentID + "-id").text(data['id'])
    $("#" + studentID + "-pdate").text(lastDate)
    $("#" + studentID + "-plength").text(lastDuration)
    $("#" + studentID + "-state").text(state)
    $("#" + studentID + "-clength").text(currentDuration)
    $("#" + studentID + "-row").hide().fadeIn(500)
}

function redrawRow(studentID) {
    $("#" + studentID + "-row").remove();
    createRow(studentID)
}

function updateRowClock(studentID, startDate) {
    currentDate = new Date()
    currentDuration = (currentDate.getTime() - startDate.getTime()) / 1000
    currentDuration = numberToTime(currentDuration)
    $("#" + studentID + "-clength").text(currentDuration)
}

function createMultipleRows(students) {
    for (var i = 0; i < students.length; i++) {
        createRow(students[i])
    }
}



$(document).ready(function() {
    $.getJSON('/api/liststudents', createMultipleRows)
});