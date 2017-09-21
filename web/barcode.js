//Reads barcode input from a handheld scanner

KEYBUFFER = []
BARCODE_LENGTH = 6

$(document).keypress(function(keyPressed) {

    if (keyPressed.which == 13) { //enter key pressed
        var code = KEYBUFFER.slice(-1 * (BARCODE_LENGTH)); //get last keys in buffer
        KEYBUFFER = []
        strbuf = ""
        $.each(code, function(key, value) { //convert keys from ASCII to a string
            strbuf += String.fromCharCode(value)
        });
        if (isNaN(strbuf)) {
            console.log('Error! Barcode is not a number! ' + strbuf)
            return
        }

        $.getJSON("/api/barcode?id=" + strbuf, barcodeSubmitCallback)

    } else {
        KEYBUFFER.push(keyPressed.which) //GitHub Issue #2
    }
});

function openStudentModal(id) {
    $("#modalTextbox").attr('name', id)
    $("#modalTextbox").val('')
    $("#student-modal-body").text("ID: " + id)
    $('#student-modal').modal('show');
}

function barcodeSubmitCallback(a) {
    if (a['id'] == null) {
        console.log('Internal server error')
        return
    }
    if (a['inDatabase'] == true) {
        console.log("Student " + a['id'] + " Successfully logged")
        redrawRow(a['id'])
    } else if (a['inDatabase'] == false) {
        console.log('Student ' + a['id'] + " does not exist in database!")
        openStudentModal(a['id'])
    }
}

function newStudentSubmitCallback(a) {
    id = this['url'].split("id=")[1]
    $.getJSON("/api/barcode?id=" + id, barcodeSubmitCallback)
}

function studentModalSubmitCallback() {
    p = {
        name: $('#modalTextbox').val(),
        id: $('#modalTextbox').attr("name")
    }
    $.get("/api/newstudent?" + $.param(p), newStudentSubmitCallback)
    $('#student-modal').modal('hide');
}

$("#modalSubmit").click(studentModalSubmitCallback)