debug = true;

function initToggleControl(id, state) {
    if (state === 'false') {
        $(id)
        .addClass('btn-success')
        .attr('action', 'false')
        .html('Turn Off');
    } else {
        $(id)
        .addClass('btn-danger')
        .attr('action', 'true')
        .html('Turn On');
    }
}

function toggleControl(id, state, text) {
    $(id)
    .toggleClass('btn-danger')
    .toggleClass('btn-success')
    .attr('action', state.toString())
    .html(text);
}

$(document).ready(function() {

    socket = io('http://127.0.0.1');

    socket.on('connect', function(data) {
        if (debug) { console.log("Client has connect to the server"); }
        $('#status').toggleClass('disconnected').toggleClass('connected');
    });

    socket.on('disconnect', function(data) {
        if (debug) { console.log("Client has disconnected from the server"); }
        $('#status').toggleClass('connected').toggleClass('disconnected');
        $.each($('.reading'), function( index, value ) {
            $(this).html('');
        });
    });

    socket.on('init', function(data) {
        if (debug) { console.log("App State", data); }
        var settings = data.settings;
        if (settings.drum_motor === 1) {
            initToggleControl('#drum-motor-btn', 'false');
        } else {
            initToggleControl('#drum-motor-btn', 'true');
        }

        if (settings.cooling_motor === 1) {
            initToggleControl('#cooling-motor-btn', 'false');
        } else {
            initToggleControl('#cooling-motor-btn', 'true');
        }

        if (settings.cooling_motor === 1) {
            initToggleControl('#solenoid-btn', 'false');
        } else {
            initToggleControl('#solenoid-btn', 'true');
        }

        $("#fan-slider" ).slider("value", settings.main_fan);
        $('#fan-handle').text(settings.main_fan);
        $("#heat-slider" ).slider("value", settings.heater);
        $('#heat-handle').text(settings.heater);
    });

    socket.on('state', function(data) {
        for (var key in data) {
            var id = "#" + key.replace('_', '-');
            $(id).html(data[key]);
        }
        chart.series[0].addPoint(data.external_temp);
        chart.series[1].addPoint(data.bean_temp);
        chart.series[2].addPoint(data.main_fan);
        chart.series[3].addPoint(data.heater);
    });

    socket.on('error', function(data) {
        console.error("Error", data);
    });

    socket.on('activity', function(data) {
        if (data.activity === "DRUM_MOTOR") {
            toggleControl('#drum-motor-btn', (!data.state), data.text);
        } else if (data.activity === "COOLING_MOTOR") {
            toggleControl('#cooling-motor-btn', (!data.state), data.text);
        } else if (data.activity === "SOLENOID") {
            toggleControl('#solenoid-btn', (!data.state), data.text);
        }
    });

    $('.mock').click(function(e) {
        if (debug) { console.log("Mock Initiated"); }
        socket.emit('mock');
    });

    $('.setup').click(function(e) {
        if (debug) { console.log("Setup Initiated"); }
        socket.emit('setup');
    });

    $('.shutdown').click(function(e) {
        if (debug) { console.log("Shutdown Initiated"); }
        socket.emit('shutdown');
        $.each($('.reading'), function( index, value ) {
            $(this).html('');
        });
    });

    $('.toggle-control').click(function(e) {
        var id = $(this).attr('id').replace('-btn', '');
        var option = $(this).attr('action');
        if (debug) { console.log(id, option); }
        socket.emit(id, option);
    });

    $("#fan-slider" ).on("slide", function(event, ui) {
        socket.emit('main-fan', ui.value);
        $('#fan-handle').text(ui.value);
    });

    $("#heat-slider" ).on("slide", function(event, ui) {
        socket.emit('heater', ui.value);
        $('#heat-handle').text(ui.value);
    });
});