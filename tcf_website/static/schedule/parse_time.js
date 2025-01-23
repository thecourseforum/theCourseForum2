/* eslint-disable no-unused-vars */ // Since these functions are called by other files

const WeekdayIndex = {
  Mo: 0,
  Tu: 1,
  We: 2,
  Th: 3,
  Fr: 4,
};

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
  const weekdayMeetingTimes = Array.from({ length: 5 }, () => []); // Monday to Friday

  for (const session of timeString) {
    const [days, startTime, , endTime] = session.split(" "); // [daysOfWeek, startTime, "-", endTime]
    const classTimePair = [stringTimeToInt(startTime), stringTimeToInt(endTime)];

    // Extract day abbreviations using regex (splitting by uppercase letters)
    const daysOfWeek = days.match(/[A-Z][a-z]?/g) || [];

    daysOfWeek.forEach((dayAbbr) => {
      const index = WeekdayIndex[dayAbbr];
      if (index !== undefined) {
        weekdayMeetingTimes[index].push(classTimePair);
      }
    });
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
  const consolidatedTimes = times;

  for (let day = 0; day < newTimeMeetingTimes.length; day++) {
    if (consolidatedTimes[day].length === 0) {
      continue;
    }
    const dayInSchedule = consolidatedTimes[day];

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
