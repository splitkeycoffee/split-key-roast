var orderChart;
var trafficChart;

$(document).ready(function() {
    var pieColors = (function() {
        var colors = [],
            base = Highcharts.getOptions().colors[0],
            i;

        for (i = 0; i < 10; i += 1) {
            // Start out with a darkened base color (negative brighten), and end
            // up with a much brighter color
            colors.push(Highcharts.Color(base).brighten((i - 3) / 7).get());
        }
        return colors;
    }());

    // orderChart = Highcharts.chart('orders', {
    //     chart: {
    //         plotBackgroundColor: null,
    //         plotBorderWidth: null,
    //         plotShadow: false,
    //         type: 'pie',
    //         height: '300px'
    //     },
    //     title: {
    //         text: 'Processed Orders'
    //     },
    //     exporting: {
    //         chartOptions: {
    //             legend: {
    //                 enabled: true
    //             }
    //         },
    //         enabled: false,
    //     },
    //     tooltip: {
    //         pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
    //     },
    //     plotOptions: {
    //         pie: {
    //             allowPointSelect: true,
    //             cursor: 'pointer',
    //             colors: pieColors,
    //             dataLabels: {
    //                 enabled: true,
    //                 format: '<b>{point.name}</b><br>{point.percentage:.1f} %',
    //                 distance: -50,
    //                 filter: {
    //                     property: 'percentage',
    //                     operator: '>',
    //                     value: 4
    //                 }
    //             }
    //         }
    //     },
    //     series: [{
    //         name: 'Orders',
    //         data: [
    //             { name: 'Unfulfilled', y: 25 },
    //             { name: 'Fulfilled', y: 75 },
    //         ]
    //     }]
    // });

    // $(function() {
    //     $.getJSON('http://www.highcharts.com/samples/data/jsonp.php?filename=analytics.csv&callback=?', function(csv) {
    //         trafficChart = Highcharts.chart('traffic', {
    //             data: {
    //                 csv: csv
    //             },
    //             chart: {
    //                 height: '300px'
    //             },
    //             exporting: {
    //                 chartOptions: {
    //                     legend: {
    //                         enabled: true
    //                     }
    //                 },
    //                 enabled: false,
    //             },
    //             title: {
    //                 text: 'Daily visits at www.highcharts.com'
    //             },
    //             xAxis: {
    //                 tickInterval: 7 * 24 * 3600 * 1000, // one week
    //                 tickWidth: 0,
    //                 gridLineWidth: 1,
    //                 labels: {
    //                     align: 'left',
    //                     x: 3,
    //                     y: -3
    //                 }
    //             },
    //             yAxis: [{ // left y axis
    //                 title: {
    //                     text: null
    //                 },
    //                 labels: {
    //                     align: 'left',
    //                     x: 3,
    //                     y: 16,
    //                     format: '{value:.,0f}'
    //                 },
    //                 showFirstLabel: false
    //             }, { // right y axis
    //                 linkedTo: 0,
    //                 gridLineWidth: 0,
    //                 opposite: true,
    //                 title: {
    //                     text: null
    //                 },
    //                 labels: {
    //                     align: 'right',
    //                     x: -3,
    //                     y: 16,
    //                     format: '{value:.,0f}'
    //                 },
    //                 showFirstLabel: false
    //             }],
    //             legend: {
    //                 align: 'left',
    //                 verticalAlign: 'top',
    //                 floating: true,
    //                 borderWidth: 0
    //             },
    //             tooltip: {
    //                 shared: true,
    //                 crosshairs: true
    //             },
    //             plotOptions: {
    //                 series: {
    //                     cursor: 'pointer',
    //                     point: {
    //                         events: {
    //                             click: function(e) {
    //                                 hs.htmlExpand(null, {
    //                                     pageOrigin: {
    //                                         x: e.pageX || e.clientX,
    //                                         y: e.pageY || e.clientY
    //                                     },
    //                                     headingText: this.series.name,
    //                                     maincontentText: Highcharts.dateFormat('%A, %b %e, %Y', this.x) + ':<br/> ' +
    //                                         this.y + ' visits',
    //                                     width: 200
    //                                 });
    //                             }
    //                         }
    //                     },
    //                     marker: {
    //                         lineWidth: 1
    //                     }
    //                 }
    //             },
    //             series: [{
    //                 name: 'All visits',
    //                 lineWidth: 4,
    //                 marker: {
    //                     radius: 4
    //                 }
    //             }, {
    //                 name: 'New visitors'
    //             }]
    //         });
    //     });
    // });
});