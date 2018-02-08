function show_me(show_id, form_name){
    // get element
    var span = document.getElementById('_new');

    // make a the span if it does not exist
    if (!span){
        span = document.createElement('span');
        span.id = '_new';
        document.getElementById(show_id).appendChild(span);
    }

    // set the value of the span
    span.innerHTML = ":<input type='number' name='' style='width:50px;' value='00' id=".concat(form_name, ">");

    // change default value to 30 minutes
    var other = document.getElementById('deflt_val');
    other.value = '30';
}

function hide_me(id_tag){
    var elem = document.getElementById(id_tag);
    if (elem) {
        elem.innerHTML = '';
    }

    // change default value to 2000m
    var other = document.getElementById('deflt_val');
    other.value = '2000';
}

function show_incomplete(bad_elem){
    var name = bad_elem.concat('-red');
    var astrix = document.getElementById(name);
    if (astrix == null){
        var span = document.createElement('span');
        span.style.color = 'red';
        span.id = name;
        span.innerHTML = "*";
        document.getElementById(bad_elem).appendChild(span);
    }
}

function addInput(form_name, pieces, mtrs_mins, secs){
    // clear current content
    document.getElementById(form_name).innerHTML = '';

    var num_pieces = document.getElementById(pieces).value;
    var w_type = document.querySelector("input[name=workout_type]:checked").value;
    var meter_minutes = document.getElementById(mtrs_mins).value;

    // verify that the 'BY' section is specified
    if (meter_minutes == ''){
        if (w_type != 'Length' || document.getElementById(secs).value == 0){
            show_incomplete('default_val_div');
            return;
        }
    }

    if (num_pieces == ''){
        window.alert('HI');
    }

    // add inputs
    for (var i = 0; i < num_pieces; i++) {
        var newdiv = document.createElement('div');
        if (w_type == 'Length'){
            var d_value_1 = document.getElementById(secs).value;
            newdiv.innerHTML = "<br>Piece " + (i + 1) + " <br><span>Time</span><input style='width:50px;' type='number' value='" + meter_minutes +
                "' name='minutes'>:<input style='width: 50px;' type='number' value='" + d_value_1 + "' name='seconds'>" +
                "<span>Meters</span><input style='width: 50px;' type='number' name='meters'>";
        }
        else {
            newdiv.innerHTML = "<br>Piece " + (i + 1) + " <br><span>Time</span><input type='number' style='width:50px;'" +
                "name='minutes'>:<input style='width:50px;' type='number' name='seconds'><span>Meters</span>" +
                "<input style='width:50px;' type='number' name='meters' value='" + meter_minutes + "'>";
        }
        document.getElementById(form_name).appendChild(newdiv);
    }

    // submit button
    var submit_div = document.createElement('div');
    submit_div.innerHTML = "<br><input type='submit' value='Save Workout'>";
    document.getElementById(form_name).appendChild(submit_div);

}