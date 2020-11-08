
let data = {
  datasets: [{
    data: [4, 3, 4, 5, 6, 7, 7, 3, 3, 4, 1, 5, 3, 6],
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
      "#B45133"
    ],
  }],
  labels: [
    "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "Drop"
  ]
}
var ctx2 = document.getElementById("myChart2");
var myChart2 = new Chart(ctx2, {
  type: 'pie',
  data: data,
  options: {
    cutoutPercentage: 65,
    responsive: false,
    legend: {
      display: false
    }
  }
});

// 57679D
// 56669C
// 55659B
// 384676
// 384676
// 374575
