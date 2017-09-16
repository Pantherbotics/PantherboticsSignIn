//Updates the clock

function zeroPad(str) {
    return ("00" + str).slice(-2)

}

function updateClock(clockID) {
    tN = new Date()
    str = zeroPad(tN.getHours()) + ":" + zeroPad(tN.getMinutes()) + ":" + zeroPad(tN.getSeconds()) + " |  " + (tN.getMonth() + 1) + "/" + tN.getDate() + "/" + tN.getFullYear()
    $("#" + clockID).text(str)
}


setInterval(updateClock, 1000, ('clock'))