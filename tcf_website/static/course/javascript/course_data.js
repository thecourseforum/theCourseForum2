let barConfig;
let pieConfig;
let myChart;
let totalSum;
const ctx = document.getElementById("myChart");

function togglePieChart() {
    if (myChart) {
        myChart.destroy();
    }
    document.getElementById("canvas-parent").style.width = "290px";
    // eslint-disable-next-line no-new,no-undef
    myChart = new Chart(ctx, pieConfig);
}

function toggleBarChart() {
    if (myChart) {
        myChart.destroy();
    }
    document.getElementById("canvas-parent").style.width = "95%";
    // eslint-disable-next-line no-new,no-undef
    myChart = new Chart(ctx, barConfig);
}

$(".pieToBar").click(function() {
    if (document.getElementById("toggle-btn").value === "bar") {
        toggleBarChart();
        document.getElementById("chart-label").className = "bottom-center";
        document.getElementById("toggle-btn").innerHTML = "Pie";
        document.getElementById("toggle-btn").value = "pie";
    } else {
        togglePieChart();
        document.getElementById("chart-label").className = "absolute-center";
        document.getElementById("toggle-btn").innerHTML = "Bar";
        document.getElementById("toggle-btn").value = "bar";
    }
});

const loadData = (data) => {
    // order in the input data
    /* eslint-disable camelcase */
    const { a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, dfw } =
    data;
    // order we want for the pie chart
    const grades_data = [
        a_plus,
        a,
        a_minus,
        b_plus,
        b,
        b_minus,
        c_plus,
        c,
        c_minus,
        dfw
    ];

    // Calculate total number of students
    totalSum = grades_data.reduce((total, num) => total + num, 0);

    // Create default pie chart
    /* eslint-enable camelcase */
    createChart(grades_data);

    const formatWorkload = (x) => `${(100 * x) / data.average_hours_per_week}%`;
    // Subtracting 0.8 from both the numerators and the denominator
    // so that the rating of 1 does look like a low one
    const formatRating = (x) => `${(100 * (x - 0.8)) / (5 - 0.8)}%`;

    // Change display if there is no data
    if (exist(data.average_gpa)) {
        $(".gpa-text").html(
            data.average_gpa === 0.0 ? "Pass/Fail" : `${data.average_gpa} GPA`
        );
    }
    if (exist(data.total_enrolled)) {
        $(".students-text").html(`${data.total_enrolled} Students`);
    } else {
        $(".students-text").remove();
        $(".chart-button").remove();
    }

    // Summary numbers
    if (exist(data.average_rating)) {
        $(".rating-num").html(data.average_rating);
    }
    if (exist(data.average_hours_per_week)) {
        $(".hours-num").html(data.average_hours_per_week);
    }
    // Rating numbers
    if (exist(data.average_instructor)) {
        $(".instructor-num").html(data.average_instructor);
    }
    if (exist(data.average_fun)) {
        $(".fun-num").html(data.average_fun);
    }
    if (exist(data.average_difficulty)) {
        $(".difficulty-num").html(data.average_difficulty);
    }
    if (exist(data.average_recommendability)) {
        $(".recommend-num").html(data.average_recommendability);
    }
    // Workload numbers
    if (exist(data.average_amount_reading)) {
        $(".reading-num").html(data.average_amount_reading);
    }
    if (exist(data.average_amount_writing)) {
        $(".writing-num").html(data.average_amount_writing);
    }
    if (exist(data.average_amount_group)) {
        $(".group-num").html(data.average_amount_group);
    }
    if (exist(data.average_amount_homework)) {
        $(".homework-num").html(data.average_amount_homework);
    }

    // Rating bars
    if (exist(data.average_instructor)) {
        $(".instructor-bar").width(formatRating(data.average_instructor));
    }
    if (exist(data.average_fun)) {
        $(".fun-bar").width(formatRating(data.average_fun));
    }
    if (exist(data.average_difficulty)) {
        $(".difficulty-bar").width(formatRating(data.average_difficulty));
    }
    if (exist(data.average_recommendability)) {
        $(".recommend-bar").width(formatRating(data.average_recommendability));
    }
    // Workload bars
    if (exist(data.average_amount_reading)) {
        $(".reading-bar").width(formatWorkload(data.average_amount_reading));
    }
    if (exist(data.average_amount_writing)) {
        $(".writing-bar").width(formatWorkload(data.average_amount_writing));
    }
    if (exist(data.average_amount_group)) {
        $(".group-bar").width(formatWorkload(data.average_amount_group));
    }
    if (exist(data.average_amount_homework)) {
        $(".homework-bar").width(formatWorkload(data.average_amount_homework));
    }
};

const createChart = (gradesData) => {
    const chartData = {
        datasets: [
            {
                data: gradesData,
                backgroundColor: [
                    "#182D66", // A+
                    "#274F97", // A
                    "#4467B6", // A-
                    "#5D83D1", // B+
                    "#6E98E4", // B
                    "#8FA9DF", // B-
                    "#DAA38E", // C+
                    "#DD734C", // C
                    "#D75626", // C-
                    "#BE4B20" // DFW
                ]
            }
        ],
        labels: ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "DFW"]
    };

    // Generate configuration for Bar Chart with chartData
    barConfig = {
        type: "bar",
        data: chartData,
        options: {
            layout: {
                padding: {
                    bottom: 20
                }
            },
            responsive: true,
            legend: {
                display: false
            },
            scales: {
                xAxes: [
                    {
                        ticks: {
                            autoSkip: false
                        },
                        gridLines: {
                            drawOnChartArea: false
                        }
                    }
                ],
                yAxes: [
                    {
                        scaleLabel: {
                            display: true,
                            labelString: "Number of Students"
                        },
                        ticks: {
                            beginAtZero: true
                        },
                        gridLines: {
                            drawOnChartArea: true
                        }
                    }
                ]
            },
            plugins: {
                labels: {
                    // render 'label', 'value', 'percentage', 'image' or custom function, default is 'percentage'
                    render: "value",

                    // font size, default is defaultFontSize
                    fontSize: 10,

                    // font color, can be color array for each data or function for dynamic color, default is defaultFontColor
                    // fontColor: "#fff",

                    // font style, default is defaultFontStyle
                    fontStyle: "normal",

                    // draw label in arc, default is false
                    // bar chart ignores this
                    arc: false,

                    // position to draw label, available value is 'default', 'border' and 'outside'
                    // bar chart ignores this
                    // default is 'default'
                    position: "default",

                    // draw label even it's overlap, default is true
                    // bar chart ignores this
                    overlap: false,

                    // add margin of text when position is `outside` or `border`
                    // default is 2
                    textMargin: 4
                }
            }
        }
    };

    // Generate configuration for Pie Chart
    pieConfig = {
        type: "pie",
        data: chartData,
        options: {
            cutoutPercentage: 65,
            responsive: true,
            aspectRatio: 1,
            tooltips: {
                callbacks: {
                    label: function(tooltipItem, data) {
                        const dataset = data.datasets[0];
                        const percent = Math.round(
                            (dataset.data[tooltipItem.index] / totalSum) * 100
                        );
                        let label = data.labels[tooltipItem.index];
                        if (tooltipItem.index === 9) {
                            label = "D/F/Withdraw";
                        }
                        return label + ": " + percent + "%";
                    }
                },
                displayColors: false
            },
            legend: {
                display: false
            },
            plugins: {
                labels: {
                    // render 'label', 'value', 'percentage', 'image' or custom function, default is 'percentage'
                    render: "label",

                    // font size, default is defaultFontSize
                    fontSize: 12,

                    // font color, can be color array for each data or function for dynamic color, default is defaultFontColor
                    fontColor: "#fff",

                    // font style, default is defaultFontStyle
                    fontStyle: "normal",

                    // draw label in arc, default is false
                    // bar chart ignores this
                    arc: false,

                    // position to draw label, available value is 'default', 'border' and 'outside'
                    // bar chart ignores this
                    // default is 'default'
                    position: "default",

                    // draw label even it's overlap, default is true
                    // bar chart ignores this
                    overlap: false,

                    // add margin of text when position is `outside` or `border`
                    // default is 2
                    textMargin: 4
                }
            }
        }
    };
    // 1. Justification for no-new: (Do not use 'new' for side effects)
    // Without disabling the warning, eslint complains about using `new` to produce side-effects.
    // (Which is how chart.js works. We can't change that.)
    // You can silence it by assigning the expression to a variable. But then, eslint complains that we have an unused variable.
    // We're not going to be able to avoid this, so I've disabled the error.
    // 2. Justification for no-undef: ('Chart' is not defined)
    // We could avoid this in the future by using WebPack or plain old ES6 modules.
    // But right now, the chart.js source is referenced in the templates themselves through a CDN,
    // so eslint will always complain. We'll just silence it.
    // eslint-disable-next-line no-new,no-undef
    myChart = new Chart(ctx, pieConfig);
};

const exist = (data) => {
    return data !== null && data !== undefined;
};
export { loadData };
