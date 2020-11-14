let loadData = async url => {
  if (url) {
    const data = await fetch(url).then(res => res.json())
    if (data.detail === "Not found.") {
      console.log("NOTFOUND")
    } else {
      const { a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, d_plus, d, d_minus, f, withdraw, drop } = data
      const grades_data = [a_plus, a, a_minus, b_plus, b, b_minus, c_plus, c, c_minus, d_plus, d, d_minus, f, withdraw, drop]
 
      createChart(grades_data)
 
      const reducer = (accumulator, currentValue) => accumulator + currentValue;
 
      document.getElementsByClassName("gpa-text")[0].innerHTML = data.average_gpa.toFixed(2) + " GPA"
      document.getElementsByClassName("students-text")[0].innerHTML = grades_data.reduce(reducer) + " Students"
 
      document.getElementsByClassName("rating_num")[0].innerHTML = data.average_rating.toFixed(2)
      document.getElementsByClassName("hours_num")[0].innerHTML = data.average_hours_per_week.toFixed(2)
 
      document.getElementsByClassName("professor-num")[0].innerHTML = data.average_instructor.toFixed(2)
      document.getElementsByClassName("fun-num")[0].innerHTML = data.average_fun.toFixed(2)
      document.getElementsByClassName("difficulty-num")[0].innerHTML = data.average_difficulty.toFixed(2)
      document.getElementsByClassName("recommend-num")[0].innerHTML = data.average_recommendability.toFixed(2)
      document.getElementsByClassName("reading-num")[0].innerHTML = data.average_amount_reading.toFixed(2)
      document.getElementsByClassName("writing-num")[0].innerHTML = data.average_amount_writing.toFixed(2)
      document.getElementsByClassName("group-num")[0].innerHTML = data.average_amount_group.toFixed(2)
      document.getElementsByClassName("homework-num")[0].innerHTML = data.average_amount_homework.toFixed(2)
 
      document.getElementsByClassName("professor-bar")[0].style.width = 100 * data.average_instructor / 5 + "%"
      document.getElementsByClassName("fun-bar")[0].style.width = 100 * data.average_fun / 5 + "%"
      document.getElementsByClassName("difficulty-bar")[0].style.width = 100 * data.average_difficulty / 5 + "%"
      document.getElementsByClassName("recommend-bar")[0].style.width = 100 * data.average_recommendability / 5 + "%"
      document.getElementsByClassName("reading-bar")[0].style.width = 100 * data.average_amount_reading / (data.average_hours_per_week) + "%"
      document.getElementsByClassName("writing-bar")[0].style.width = 100 * data.average_amount_writing / data.average_hours_per_week + "%"
      document.getElementsByClassName("group-bar")[0].style.width = 100 * data.average_amount_group / data.average_hours_per_week + "%"
      document.getElementsByClassName("homework-bar")[0].style.width = 100 * data.average_amount_homework / data.average_hours_per_week + "%"
    }
  }
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
        "#a34022"
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