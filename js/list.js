
function getFromDB(path, _callback) {

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            _callback(xmlHttp.responseText);
        }
    }
    xmlHttp.open("GET", 'http://127.0.0.1:5000' + path, true); 
    xmlHttp.send(null);
}

function populateTable(data) {
    if (!data) {
        getFromDB('/table', populateTable);
    } else {
        var stadiums = eval(data);

        stadiums.forEach( function(stad) {
            var basics = stad['basics'];
            var cur = stad['cur_week'];
            var prev = stad['prev_week'];

            document.getElementById('stadiums-append-zone').innerHTML += "<tr><td>"+ basics[1] +"</td><td>"+ basics[2] +"</td><td>"+ 
            "rating" +"</td><td>"+ "change_ratings" +"</td><td>"+ "#ratings" +"</td><td>"+ "change_#ratings" +"</td><td>"+ 
            "visits" +"</td><td>"+ "change_visits" +"</td><td>"+ "avg$" +"</td><td>"+ "change_$" +"</td><td>"+ 
            "atten" +"</td><td>"+ "change_atten" +"</td><td>"+ "avg%filled" +"</td><td>"+
            basics[3] +"</td><td>"+ basics[5] +"</td><td>"+ (basics[6]/basics[5]*100).toFixed(2) +"</td></tr>";
        });
    }
}

window.onload = function() {

  populateTable();
  $("#stadiums").stupidtable();
};