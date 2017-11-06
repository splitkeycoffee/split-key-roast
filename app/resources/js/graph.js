var chart;

$(document).ready(function () {
    Highcharts.setOptions({
        global: {
            useUTC: false
        }
    });

    chart = Highcharts.chart('container', {
        chart: {
            type: 'spline',
            animation: Highcharts.svg, // don't animate in old IE
            marginRight: 10
        },
        title: {
            text: 'R1'
        },
        xAxis: {
            title: {
                text: 'Minutes'
            },
            type: 'datetime',
            tickPixelInterval: 150
        },
        yAxis: {
            title: {
                text: 'Temperature'
            },
            max: 450,
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        plotOptions: {
            areaspline: {
                fillOpacity: 0.5
            }
        },
        tooltip: {
            formatter: function () {
                return '<b>' + this.series.name + '</b><br/>' +
                    Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', this.x) + '<br/>' +
                    Highcharts.numberFormat(this.y, -1);
            }
        },
        legend: {
            enabled: false
        },
        exporting: {
            enabled: true
        },
        series: [{
            name: 'ET',
            data: []
        }, {
            name: 'BT',
            data: []
        }, {
            name: 'Fan',
            type: 'spline',
            dashStyle: 'dash',
            data: []
        }, {
            name: 'Heat',
            type: 'spline',
            dashStyle: 'dash',
            data: []
        }]
    });
});
