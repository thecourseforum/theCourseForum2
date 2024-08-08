/* eslint-disable */

function stringTimeToInt(stringTime) {
  let ret = 0;
  parsed_time = stringTime.split(":");
  ret += 60 * parseInt(parsed_time[0]);
  if (parsed_time[1][2] == "p" && parsed_time[0] != "12") {
    ret += 720;
  }
  minute_string = parsed_time[1].substr(0, 2);
  ret += parseInt(minute_string);

  return ret;
}

function parseTime(time_string) {
  time_string = time_string.split(","); //split lab times / discussion times / lecture times
  let weekday_meeting_times = Array.apply(null, Array(5)).map(function () {}); //index 0 = monday, index 1 = tuesday, index 2 = wednesday, index 3 = thursday, index 4 = friday
  for (let i = 0; i < weekday_meeting_times.length; i++) {
    weekday_meeting_times[i] = [];
  }

  for (let j = 0; j < time_string.length; j++) {
    let meetingTime = time_string[j].split(" "); //creates an array that contains[days_of_week, class_start_time, -, class_end_time]
    let days_of_week = meetingTime[0];

    while (days_of_week != "") {
      //adds both the start and end time for a particular class to a weekday
      let class_time_pair = [
        stringTimeToInt(meetingTime[1]),
        stringTimeToInt(meetingTime[3]),
      ];

      if (days_of_week.includes("Mo")) {
        weekday_meeting_times[0].push(class_time_pair);
        days_of_week = days_of_week.replace("Mo", "");
      }
      if (days_of_week.includes("Tu")) {
        weekday_meeting_times[1].push(class_time_pair);
        days_of_week = days_of_week.replace("Tu", "");
      }
      if (days_of_week.includes("We")) {
        weekday_meeting_times[2].push(class_time_pair);
        days_of_week = days_of_week.replace("We", "");
      }
      if (days_of_week.includes("Th")) {
        weekday_meeting_times[3].push(class_time_pair);
        days_of_week = days_of_week.replace("Th", "");
      }
      if (days_of_week.includes("Fr")) {
        weekday_meeting_times[4].push(class_time_pair);
        days_of_week = days_of_week.replace("Fr", "");
      }
    }
  }
  return weekday_meeting_times;
}

function consolidateTimes(times) {
  selected_classes_meeting_times = [[], [], [], [], []];
  for (
    var selected_class = 0;
    selected_class < times.length;
    selected_class++
  ) {
    class_meeting_times = parseTime(times[selected_class]);
    for (var i = 0; i < class_meeting_times.length; i++) {
      if (class_meeting_times[i].length == 0) {
        continue;
      }
      selected_classes_meeting_times[i].push(class_meeting_times[i]);
    }
  }
  return selected_classes_meeting_times;
}

function checkConflict(newTime, times) {
  // this method will return true if there is conflict with the list of times passed in and the newTime
  new_time_meeting_times = parseTime(newTime);
  consolidated_times = times;

  for (var day = 0; day < new_time_meeting_times.length; day++) {
    if (consolidated_times[day].length == 0) {
      continue;
    }
    dayInSchedule = consolidated_times[day];

    if (new_time_meeting_times[day].length == 0 || dayInSchedule.length == 0) {
      // skip over empty days in new time meeting times
      continue;
    }

    for (
      var period = 0;
      period < new_time_meeting_times[day].length;
      period++
    ) {
      // period for proposed class
      for (
        var period_in_schedule = 0;
        period_in_schedule < dayInSchedule.length;
        period_in_schedule++
      ) {
        // period_in for exisiting schedule
        var beginsBefore =
          new_time_meeting_times[day][period][0] <=
          dayInSchedule[period_in_schedule][0][1];
        var endsAfter =
          new_time_meeting_times[day][period][1] >=
          dayInSchedule[period_in_schedule][0][0];
        if (beginsBefore && endsAfter) {
          return true;
        }
      }
    }
  }
  return false;
}

function addTimeBlock(newTime, schedule) {
  // this method will add the time block to a schedule HTML element
  // TODO: implement this method, NOTE: there can be many ways to do, this is just a starter code

  return true;
}
