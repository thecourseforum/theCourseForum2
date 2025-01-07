/* eslint-disable no-unused-vars */ // Since these functions are called by other files
function stringTimeToInt(stringTime) {
  let ret = 0;
  const parsedTime = stringTime.split(":");
  ret += 60 * parseInt(parsedTime[0]);
  if (parsedTime[1][2] === "p" && parsedTime[0] !== "12") {
    ret += 720;
  }
  const minuteString = parsedTime[1].substr(0, 2);
  ret += parseInt(minuteString);

  return ret;
}

function parseTime(timeString) {
  timeString = timeString.split(","); // split lab times / discussion times / lecture times
  const weekdayMeetingTimes = Array.from({ length: 5 }, () => []); // index 0 = monday, index 1 = tuesday, index 2 = wednesday, index 3 = thursday, index 4 = friday

  for (let j = 0; j < timeString.length; j++) {
    const meetingTime = timeString[j].split(" "); // creates an array that contains[daysOfWeek, class_start_time, -, class_end_time]
    let daysOfWeek = meetingTime[0];

    while (daysOfWeek !== "") {
      // adds both the start and end time for a particular class to a weekday
      const classTimePair = [
        stringTimeToInt(meetingTime[1]),
        stringTimeToInt(meetingTime[3]),
      ];

      if (daysOfWeek.includes("Mo")) {
        weekdayMeetingTimes[0].push(classTimePair);
        daysOfWeek = daysOfWeek.replace("Mo", "");
      }
      if (daysOfWeek.includes("Tu")) {
        weekdayMeetingTimes[1].push(classTimePair);
        daysOfWeek = daysOfWeek.replace("Tu", "");
      }
      if (daysOfWeek.includes("We")) {
        weekdayMeetingTimes[2].push(classTimePair);
        daysOfWeek = daysOfWeek.replace("We", "");
      }
      if (daysOfWeek.includes("Th")) {
        weekdayMeetingTimes[3].push(classTimePair);
        daysOfWeek = daysOfWeek.replace("Th", "");
      }
      if (daysOfWeek.includes("Fr")) {
        weekdayMeetingTimes[4].push(classTimePair);
        daysOfWeek = daysOfWeek.replace("Fr", "");
      }
    }
  }
  return weekdayMeetingTimes;
}

function consolidateTimes(times) {
  const selectedClassesMeetingTimes = [[], [], [], [], []];
  for (let selectedClass = 0; selectedClass < times.length; selectedClass++) {
    const classMeetingTimes = parseTime(times[selectedClass]);
    for (let i = 0; i < classMeetingTimes.length; i++) {
      if (classMeetingTimes[i].length === 0) {
        continue;
      }
      selectedClassesMeetingTimes[i].push(classMeetingTimes[i]);
    }
  }
  return selectedClassesMeetingTimes;
}

function checkConflict(newTime, times) {
  // this method will return true if there is conflict with the list of times passed in and the newTime
  const newTimeMeetingTimes = parseTime(newTime);
  const consolidatedRimes = times;

  for (let day = 0; day < newTimeMeetingTimes.length; day++) {
    if (consolidatedRimes[day].length === 0) {
      continue;
    }
    const dayInSchedule = consolidatedRimes[day];

    if (newTimeMeetingTimes[day].length === 0 || dayInSchedule.length === 0) {
      // skip over empty days in new time meeting times
      continue;
    }

    for (let period = 0; period < newTimeMeetingTimes[day].length; period++) {
      // period for proposed class
      for (
        let periodInSchedule = 0;
        periodInSchedule < dayInSchedule.length;
        periodInSchedule++
      ) {
        // period_in for exisiting schedule
        const beginsBefore =
          newTimeMeetingTimes[day][period][0] <=
          dayInSchedule[periodInSchedule][0][1];
        const endsAfter =
          newTimeMeetingTimes[day][period][1] >=
          dayInSchedule[periodInSchedule][0][0];
        if (beginsBefore && endsAfter) {
          return true;
        }
      }
    }
  }
  return false;
}
