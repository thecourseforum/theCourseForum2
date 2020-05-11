const sort_by_votes = () => {
    if (!$('#votes-sort-btn').hasClass('active')) {
      $('#recent-sort-btn').removeClass('active')
      $('#highrating-sort-btn').removeClass('active')
      $('#lowrating-sort-btn').removeClass('active')

      $('#votes-sort-btn').addClass('active')
      $('#review-sort-select').html("Most Helpful")
      sort_reviews("votes");
    }
}

const sort_by_recent = () => {
    if (!$('#recent-sort-btn').hasClass('active')) {
      $('#votes-sort-btn').removeClass('active')
      $('#highrating-sort-btn').removeClass('active')
      $('#lowrating-sort-btn').removeClass('active')

      $('#recent-sort-btn').addClass('active')
      $('#review-sort-select').html("Most Recent")
      sort_reviews("recent");
    }
}

const sort_by_highrating = () => {
  if (!$('#highrating-sort-btn').hasClass('active')) {
    $('#votes-sort-btn').removeClass('active')
    $('#recent-sort-btn').removeClass('active')
    $('#lowrating-sort-btn').removeClass('active')

    $('#highrating-sort-btn').addClass('active')
    $('#review-sort-select').html("Highest Rating")
    sort_reviews("high-rating");
  }
}

const sort_by_lowrating = () => {
    if (!$('#lowrating-sort-btn').hasClass('active')) {
      $('#votes-sort-btn').removeClass('active')
      $('#recent-sort-btn').removeClass('active')
      $('#highrating-sort-btn').removeClass('active')

      $('#lowrating-sort-btn').addClass('active')
      $('#review-sort-select').html("Lowest Rating")
      sort_reviews("low-rating");
    }
}

const sort_reviews = (prop) => {
    cmp = cmp_prop(prop);
    var reviews = $(".review");
    reviews.detach().sort(cmp);
    $('.reviews').append(reviews);
}

function date_to_int(date_str){
  date = new Date(date_str);
  return date.getTime();
}

function cmp_prop(prop) {
    p="";
    switch (prop) {
      case "votes":
        p = "vote-count";
        break;
      case "recent":
        p = "date";
        break;
      case "high-rating":
        p = "review-average";
        break;
      case "low-rating":
        p = "review-average";
        break;
    }

    x=1;
    if(prop=="low-rating"){
      x = -1;
    }
    return function(a, b) {
      val_a = a.querySelector('#'.concat(p)).innerHTML.trim();
      val_b = b.querySelector('#'.concat(p)).innerHTML.trim();

      if(prop=="recent"){
        val_a = date_to_int(val_a);
        val_b = date_to_int(val_b);
      }

      if (val_a > val_b) {
          return -1*x;
      } else if (val_a < val_b) {
          return 1*x;
      } else {
          return 0;
      }
    }
}

$(window).on('load', function() {
  sort_by_votes();
});
