
let loadData = data => {
    const { a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, d_plus, d, d_minus, f, withdraw, drop } = data
    const grades_data = [a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, d_plus, d, d_minus, f, withdraw, drop]

    console.log(data)

    createChart(grades_data)

    data.average_gpa !== null ? document.getElementsByClassName("gpa-text")[0].innerHTML = data.average_gpa + " GPA" : null
    grades_data !== null ? document.getElementsByClassName("students-text")[0].innerHTML = data.total_enrolled + " Students" : null

    data.average_rating !== null ? document.getElementsByClassName("rating-num")[0].innerHTML = data.average_rating : null
    data.average_hours_per_week !== null ? document.getElementsByClassName("hours-num")[0].innerHTML = data.average_hours_per_week : null

    data.average_instructor !== null ? document.getElementsByClassName("instructor-num")[0].innerHTML = data.average_instructor : null
    data.average_fun !== null ? document.getElementsByClassName("fun-num")[0].innerHTML = data.average_fun : null
    data.average_difficulty !== null ? document.getElementsByClassName("difficulty-num")[0].innerHTML = data.average_difficulty : null
    data.average_recommendability !== null ? document.getElementsByClassName("recommend-num")[0].innerHTML = data.average_recommendability : null
    data.average_amount_reading !== null ? document.getElementsByClassName("reading-num")[0].innerHTML = data.average_amount_reading : null
    data.average_amount_writing !== null ? document.getElementsByClassName("writing-num")[0].innerHTML = data.average_amount_writing : null
    data.average_amount_group !== null ? document.getElementsByClassName("group-num")[0].innerHTML = data.average_amount_group : null
    data.average_amount_homework !== null ? document.getElementsByClassName("homework-num")[0].innerHTML = data.average_amount_homework : null

    data.average_instructor !== null ? document.getElementsByClassName("instructor-bar")[0].style.width = 100 * (data.average_instructor - .8) / 4.2 + "%" : null
    data.average_fun !== null ? document.getElementsByClassName("fun-bar")[0].style.width = 100 * (data.average_fun - .8) / 4.2 + "%" : null
    data.average_difficulty !== null ? document.getElementsByClassName("difficulty-bar")[0].style.width = 100 * (data.average_difficulty-.8) / 4.2 + "%" : null
    data.average_recommendability !== null ? document.getElementsByClassName("recommend-bar")[0].style.width = 100 * (data.average_recommendability-.8) / 4.2 + "%" : null
    data.average_amount_reading !== null ? document.getElementsByClassName("reading-bar")[0].style.width = 100 * data.average_amount_reading / (data.average_hours_per_week) + "%" : null
    data.average_amount_writing !== null ? document.getElementsByClassName("writing-bar")[0].style.width = 100 * data.average_amount_writing / data.average_hours_per_week + "%" : null
    data.average_amount_group !== null ? document.getElementsByClassName("group-bar")[0].style.width = 100 * data.average_amount_group / data.average_hours_per_week + "%" : null
    data.average_amount_homework !== null ? document.getElementsByClassName("homework-bar")[0].style.width = 100 * data.average_amount_homework / data.average_hours_per_week + "%" : null
}

let createChart = grades_data => {
  let chart_data = {
    datasets: [{
      data: grades_data,
      backgroundColor: [
        '#57679D',
        '#56669C',
        '#55659B',
        '#384676',
        '#384676',
        '#374575',
        "#364474",
        "#18244B",
        "#17234A",
        "#162249",
        "#E06A45",
        "#DE6843",
        "#C95F36",
        "#B45133",
        "#b35032"
      ],
    }],
    labels: [
      "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "Withdraw", "Drop"
    ]
  }
  var ctx = document.getElementById("myChart");
  var myChart = new Chart(ctx, {
    type: 'pie',
    data: chart_data,
    options: {
      cutoutPercentage: 65,
      responsive: true,
      aspectRatio: 1,
      legend: {
        display: false
      },
      plugins: {
        labels: {
          // render 'label', 'value', 'percentage', 'image' or custom function, default is 'percentage'
          render: 'label',

          // font size, default is defaultFontSize
          fontSize: 12,

          // font color, can be color array for each data or function for dynamic color, default is defaultFontColor
          fontColor: '#fff',

          // font style, default is defaultFontStyle
          fontStyle: 'normal',

          // draw label in arc, default is false
          // bar chart ignores this
          arc: false,

          // position to draw label, available value is 'default', 'border' and 'outside'
          // bar chart ignores this
          // default is 'default'
          position: 'default',

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
}

export { loadData }