var mainChart;
var auxChart;

$(document).ready(function () {
    Highcharts.getSVG = function(charts, options, callback) {
        var svgArr = [],
            top = 10,
            width = 10,
            addSVG = function(svgres) {
                var svgWidth = +svgres.match(
                        /^<svg[^>]*width\s*=\s*\"?(\d+)\"?[^>]*>/
                    )[1],
                    svgHeight = +svgres.match(
                        /^<svg[^>]*height\s*=\s*\"?(\d+)\"?[^>]*>/
                    )[1],
                    // Offset the position of this chart in the final SVG
                    svg = svgres.replace('<svg', '<g transform="translate(10,' + top + ')" ');
                svg = svg.replace('</svg>', '</g>');
                top += svgHeight + 10;
                width = Math.max(width, svgWidth) + 10;
                svgArr.push(svg);
            },
            exportChart = function(i) {
                if (i === charts.length) {
                    return callback('<svg height="' + top + '" width="' + width +
                        '" version="1.1" xmlns="http://www.w3.org/2000/svg">' + svgArr.join('') + '</svg>');
                }
                charts[i].getSVGForLocalExport(options, {}, function() {
                    console.log("Failed to get SVG");
                }, function(svg) {
                    addSVG(svg);
                    return exportChart(i + 1); // Export next only when this SVG is received
                });
            };
        exportChart(0);
    };

    Highcharts.exportCharts = function (charts, options) {
        options = Highcharts.merge(Highcharts.getOptions().exporting, options);
        Highcharts.getSVG(charts, options, function (svg) {
            Highcharts.downloadSVGLocal(svg, options, function () {
                console.log("Failed to export on client side");
            });
        });
    };

    $('#container').bind('mousemove touchmove touchstart', function(e) {
        var chart,
            point,
            i,
            event;

        for (i = 0; i < Highcharts.charts.length; i = i + 1) {
            chart = Highcharts.charts[i];
            event = chart.pointer.normalize(e.originalEvent); // Find coordinates within the chart
            points = [chart.series[0].searchPoint(event, true),
                      chart.series[1].searchPoint(event, true)]; // Get the hovered point

            if (points[0] && points[1]) {
                points[0].onMouseOver(); // Show the hover marker
                points[1].onMouseOver(); // Show the hover marker
                chart.tooltip.refresh(points); // Show the tooltip
                chart.xAxis[0].drawCrosshair(e, points[0]); // Show the crosshair
            }
        }
    });

    Highcharts.setOptions({
        exporting: {
            fallbackToExportServer: false // Ensure the export happens on the client side or not at all
        },
        global: {
            useUTC: false
        },
        tooltip: {
            shared: true,
            formatter: function () {
                if (this.point) {
                    return '';
                }
                return '<b>' + this.points[0].series.name + ':</b> ' + Highcharts.numberFormat(this.points[0].y, -1) + '<br/>' +
                        '<b>' + this.points[1].series.name + ':</b> ' + Highcharts.numberFormat(this.points[1].y, -1) + '<br/>';
            },
            borderColor: '#000000',
            style: {
                fontSize: '16px'
            }
        },
        title: {
            text: ''
        },
        legend: {
            enabled: false
        }
    });

    mainChart = Highcharts.chart('container', {
        chart: {
            type: 'spline',
            animation: Highcharts.svg,
            backgroundColor: {
                linearGradient: { x1: 0, x2: 0, y1: 0, y2: 1 },
                stops: [
                    [0, '#ffffff'],
                    [.150, '#ffffff'],
                    [.151, '#efe8e0'],
                    [.304, '#efe8e0'],
                    [.305, '#fef1da'],
                    [.509, '#fef1da'],
                    [.510, '#d9ebd9'],
                    [.730, '#d9ebd9'],
                    [.100, '#ffffff']
                ]
            },
        },
        title: {
            text: ''
        },
        xAxis: {
            title: {
                text: ''
            },
            max: 15,
            min: 0,
            gridLineColor: '#e5e5e5',
            gridLineWidth: 1,
        },
        yAxis: {
            title: {
                text: 'Temperature'
            },
            min: 0,
            max: 550,
            gridLineColor: '#e5e5e5',
        },
        exporting:{
            chartOptions:{
                legend:{
                    enabled:true
                }
            },
            enabled: false,
            sourceWidth: 1200,
            sourceHeight: 600
        },
        series: [{
            name: 'Environment Temperature',
            color: 'red',
            data: [],
            id: 'et'
        }, {
            name: 'Bean Temperature',
            color: '#020c7d',
            data: [],
            id: 'bt'
        }, {
            type: 'flags',
            shape: 'squarepin',
            data: [],
            onSeries: 'bt',
            yAxis: 0
        }]
    });

    auxChart = Highcharts.chart('auxiliary', {
        chart: {
            type: 'spline',
            animation: Highcharts.svg,
            backgroundColor: '#f5f5f5',
        },
        xAxis: {
            max: 15,
            min: 0,
            title: {
                'text': 'Minutes'
            }
        },
        yAxis: {
            max: 110,
            gridLineColor: '#e5e5e5',
            title: {
                text: 'Power'
            },
        },
        exporting:{
            chartOptions:{
                legend:{
                    enabled:true
                }
            },
            enabled: false,
            sourceWidth: 1200,
            sourceHeight: 200
        },
        series: [{
            name: 'Fan',
            type: 'spline',
            // dashStyle: 'dash',
            data: []
        }, {
            name: 'Heat',
            type: 'spline',
            // dashStyle: 'dash',
            data: []
        }]
    });

    $('#export-png').click(function () {
      Highcharts.exportCharts([mainChart, auxChart]);
    });
});
