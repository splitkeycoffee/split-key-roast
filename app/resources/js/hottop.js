socket = null;
debug = true;
plotCharge = false;
plotTurningPoint = false;

function initToggleControl(id, state) {
    if (state === 'false') {
        $(id)
        .addClass('btn-success')
        .attr('action', 'false')
        .html('Turn Off');
    } else {
        $(id)
        .addClass('btn-warning')
        .attr('action', 'true')
        .html('Turn On');
    }
}

function toggleControl(id, state, text) {
    $(id)
    .toggleClass('btn-warning')
    .toggleClass('btn-success')
    .attr('action', state.toString())
    .html(text);
}

$(document).ready(function() {

    socket = io('http://127.0.0.1');

    socket.on('connect', function(data) {
        if (debug) { console.log("Client has connect to the server"); }
    });

    socket.on('disconnect', function(data) {
        if (debug) { console.log("Client has disconnected from the server"); }
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

        $("#fan-slider").slider("value", 0);
        $('#fan-handle').text(0);
        $("#heat-slider").slider("value", 0);
        $('#heat-handle').text(0);
        $("#fan-slider").slider("disable");
        $("#heat-slider").slider("disable");
    });

    socket.on('state', function(data) {
        if (data.roasting && data.roast.record) {
            $('.mock').prop("disabled", true);
            $('.setup').prop("disabled", true);
            $('.shutdown').prop("disabled", true);
            $('.start-monitor').prop("disabled", true);
            $('.stop-monitor').prop("disabled", false);
            $('.reset').prop("disabled", true);
            $("#fan-slider").slider("enable");
            $("#heat-slider").slider("enable");
        } else if (data.roasting) {
            $('.mock').prop("disabled", true);
            $('.setup').prop("disabled", true);
            $('.shutdown').prop("disabled", false);
            $('.start-monitor').prop("disabled", false);
            $('.stop-monitor').prop("disabled", false);
            $('.reset').prop("disabled", false);
            $("#fan-slider").slider("enable");
            $("#heat-slider").slider("enable");
        } else {
            $('.shutdown').prop("disabled", true);
            $('.mock').prop("disabled", false);
            $('.setup').prop("disabled", false);
            $('.start-monitor').prop("disabled", true);
            $('.stop-monitor').prop("disabled", true);
            $('.reset').prop("disabled", true);
            $("#fan-slider").slider("value", 0);
            $('#fan-handle').text(0);
            $("#heat-slider").slider("value", 0);
            $('#heat-handle').text(0);
            $("#fan-slider").slider("disable");
            $("#heat-slider").slider("disable");
        }

        for (var key in data.config) {
            var id = "#" + key.replace('_', '-');
            if (key === 'environment_temp' || key === 'bean_temp') {
                $(id).html(data.config[key].toFixed(2));
            } else {
                $(id).html(data.config[key]);
            }
        }

        if (!data.roast.record) {
            return false;
        }

        if (data.roast.charge && !plotCharge) {
            mainChart.series[2].addPoint({
                x: data.roast.charge.time,
                title: 'C (' + data.roast.charge.bean_temp.toFixed(0) + ")",
                text: "Charge"
            });
            plotCharge = true;
        }

        if (data.roast.turning_point && !plotTurningPoint) {
            mainChart.series[2].addPoint({
                x: data.roast.turning_point.time,
                title: 'TP (' + data.roast.turning_point.bean_temp.toFixed(0) + ")",
                text: "Turning Point"
            });
            plotTurningPoint = true;
        }

        mainChart.series[0].addPoint([data.time, data.config.environment_temp]);
        mainChart.series[1].addPoint([data.time, data.config.bean_temp]);
        if (data.config.delta_bean_temp){
            mainChart.series[3].addPoint([data.alt_time, data.config.delta_bean_temp]);
        }
        // Normalize the fan data set to match the scale of heat
        auxChart.series[0].addPoint([data.time, data.config.main_fan * 10]);
        auxChart.series[1].addPoint([data.time, data.config.heater]);
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
        } else if (data.activity === "ROAST_START") {
            $('.mock').prop("disabled", true);
            $('.setup').prop("disabled", true);
            $('.reset').prop("disabled", true);
            $('#connection-status').toggleClass('disconnected').toggleClass('connected');
        } else if (data.activity === "ROAST_RESET") {
            location.reload();
        } else if (data.activity === "ROAST_SHUTDOWN") {
            var subtitle = $('#graph-subtitle').val();
            mainChart.setTitle({text: $('#graph-title').val()}, {text: subtitle});
            $('.mock').prop("disabled", false);
            $('.setup').prop("disabled", false);
            $('#connection-status').toggleClass('connected').toggleClass('disconnected');
            $('.start-monitor').prop("disabled", true);
            $('.stop-monitor').prop("disabled", true);
            $('.reset').prop("disabled", false);
            $("#fan-slider").slider("disable");
            $("#heat-slider").slider("disable");
        } else if (data.activity === "DRY_END") {
            mainChart.series[2].addPoint({
                x: data.state.last.time,
                title: 'DE (' + data.state.last.bean_temp.toFixed(0) + ")",
                text: "Dry End"
            });
        } else if (data.activity === "FIRST_CRACK") {
            mainChart.series[2].addPoint({
                x: data.state.last.time,
                title: 'FC (' + data.state.last.bean_temp.toFixed(0) + ")",
                text: "First Crack"
            });
        } else if (data.activity === "SECOND_CRACK") {
            mainChart.series[2].addPoint({
                x: data.state.last.time,
                title: 'SC (' + data.state.last.bean_temp.toFixed(0) + ")",
                text: "Second Crack"
            });
        } else if (data.activity === "DROP_COFFEE") {
            mainChart.series[2].addPoint({
                x: data.state.last.time,
                title: 'D (' + data.state.last.bean_temp.toFixed(0) + ")",
                text: "Dropped"
            });
        } else if (data.activity === "START_MONITOR") {
            $('#monitor-status').toggleClass('disconnected').toggleClass('connected');
            $('.start-monitor').prop("disabled", true);
            $('.shutdown').prop("disabled", true);
        } else if (data.activity === "STOP_MONITOR") {
            $('#monitor-status').toggleClass('connected').toggleClass('disconnected');
            $('.start-monitor').prop("disabled", false);
            $('.shutdown').prop("disabled", false);
        } else {
            console.log(data);
        }
    });

    $('.mock').click(function(e) {
        if (debug) { console.log("Mock Initiated"); }
        socket.emit('mock');
    });

    $('.setup').click(function(e) {
        if (debug) { console.log("Setup Initiated"); }
        socket.emit('roaster-setup');
    });

    $('.shutdown').click(function(e) {
        if (debug) { console.log("Shutdown Initiated"); }
        socket.emit('roaster-shutdown');
        $.each($('.reading'), function( index, value ) {
            $(this).html('-1');
        });
    });

    $('.start-monitor').click(function(e) {
        if (debug) { console.log("Monitoring begins"); }
        socket.emit('start-monitor');
        stopwatch.start();
    });

    $('.stop-monitor').click(function(e) {
        if (debug) { console.log("Monitoring ends"); }
        socket.emit('stop-monitor');
        stopwatch.stop();
    });

    $('.dry-end').click(function() {
        socket.emit('dry-end');
        $(this).prop("disabled", true);
    });

    $('.fc').click(function() {
        socket.emit('first-crack');
        $(this).prop("disabled", true);
    });

    $('.sc').click(function() {
        socket.emit('second-crack');
        $(this).prop("disabled", true);
    });

    $('.drop').click(function() {
        if (debug) { console.log("Drop Initiated"); }
        socket.emit('drop');
        $(this).prop("disabled", true);
        $("#drum-motor-btn")
        .removeClass('btn-success')
        .addClass('btn-warning')
        .attr('action', 'true')
        .prop("disabled", true)
        .html('Turn On');
        $("#cooling-motor-btn")
        .addClass('btn-success')
        .removeClass('btn-warning')
        .attr('action', 'true')
        .prop("disabled", true)
        .html('Turn Off');
        $("#heat-slider").slider("value", 0);
        $('#heat-handle').text(0);
        $("#fan-slider").slider("value", 10);
        $('#fan-handle').text(10);
        $('#cooldown-alert').show();
    });

    $('.sec-control').click(function(e) {
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

    $('.reset').click(function() {
        socket.emit('reset', properties);
    });
});