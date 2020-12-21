const loadData = data => {
    const { a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, d_plus, d, d_minus, f, ot, drop, withdraw } = data;
    const grades_data = [a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, d_plus, d, d_minus, f, ot, drop, withdraw ];

    createChart(grades_data);
    
    const formatWorkload = x => `${100 * x / data.average_hours_per_week}%`;
    // Subtracting 0.8 from both the numerators and the denominator
    // so that the rating of 1 does look like a low one
    const formatRating = x => `${100 * (x - 0.8) / (5 - 0.8)}%`;

    // Pie chart
    if (exist(data.average_gpa))
        $(".gpa-text").html(data.average_gpa == 0.0 ? "Pass/Fail" : `${data.average_gpa} GPA`);
    if(exist(data.total_enrolled))
        $(".students-text").html(`${data.total_enrolled} Students`);
    else
        $(".students-text").remove();

    // Summary numbers
    if(exist(data.average_rating))
        $(".rating-num").html(data.average_rating);
    if(exist(data.average_hours_per_week))
        $(".hours-num").html(data.average_hours_per_week);
    // Rating numbers
    if(exist(data.average_instructor))
        $(".instructor-num").html(data.average_instructor);
    if(exist(data.average_fun))
        $(".fun-num").html(data.average_fun);
    if(exist(data.average_difficulty))
        $(".difficulty-num").html(data.average_difficulty);
    if(exist(data.average_recommendability))
        $(".recommend-num").html(data.average_recommendability);
    // Workload numbers
    if(exist(data.average_amount_reading))
        $(".reading-num").html(data.average_amount_reading);
    if(exist(data.average_amount_writing))
        $(".writing-num").html(data.average_amount_writing);
    if(exist(data.average_amount_group))
        $(".group-num").html(data.average_amount_group);
    if(exist(data.average_amount_homework))
        $(".homework-num").html(data.average_amount_homework);

    // Rating bars
    if(exist(data.average_instructor))
        $(".instructor-bar").width(formatRating(data.average_instructor));
    if(exist(data.average_fun))
        $(".fun-bar").width(formatRating(data.average_fun));
    if(exist(data.average_difficulty))
        $(".difficulty-bar").width(formatRating(data.average_difficulty));
    if(exist(data.average_recommendability))
        $(".recommend-bar").width(formatRating(data.average_recommendability));
    // Workload bars
    if(exist(data.average_amount_reading))
        $(".reading-bar").width(formatWorkload(data.average_amount_reading));
    if(exist(data.average_amount_writing))
        $(".writing-bar").width(formatWorkload(data.average_amount_writing));
    if(exist(data.average_amount_group))
        $(".group-bar").width(formatWorkload(data.average_amount_group));
    if(exist(data.average_amount_homework))
        $(".homework-bar").width(formatWorkload(data.average_amount_homework));
};

const createChart = grades_data => {
    const chart_data = {
        datasets: [{
            data: grades_data,
            backgroundColor: [
                "#57679D",  // A+
                "#56669C",  // A
                "#55659B",  // A-
                "#384676",  // B+
                "#384676",  // B
                "#374575",  // B-
                "#364474",  // C+
                "#18244B",  // C
                "#17234A",  // C-
                "#162249",  // D+
                "#E06A45",  // D
                "#DE6843",  // D-
                "#C95F36",  // F
                "#666600",  // Other
                "#B45133",  // Drop
                "#b35032",  // Withdraw
            ]
        }],
        labels: [
            "A+", "A", "A-", "B+", "B", "B-",
            "C+", "C", "C-", "D+", "D", "D-",
            "F", "Pass", "Drop", "Withdraw",
        ]
    };
    var ctx = document.getElementById("myChart");
    new Chart(ctx, {
        type: "pie",
        data: chart_data,
        options: {
            cutoutPercentage: 65,
            responsive: true,
            aspectRatio: 1,
            tooltips: {
                callbacks: {
                    label: function(tooltipItem, data) {
                        var dataset = data.datasets[0];
                        var percent = Math.round((dataset.data[tooltipItem.index] / dataset._meta[0].total) * 100);
                        return data.labels[tooltipItem.index] + ": " + percent + "%";
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
    });
};

const exist = data => {
    return data !== null && data !== undefined;
};
export { loadData };
