/* eslint-disable */

function parseTime(time_string) {
    time_string = time_string.split(","); //split lab times / discussion times / lecture times
    let weekday_meeting_times = Array.apply(null, Array(5)).map(function () {}) //index 0 = monday, index 1 = tuesday, index 2 = wednesday, index 3 = thursday, index 4 = friday
    for(let i=0; i<weekday_meeting_times.length;i++)
    {
        weekday_meeting_times[i] = [];
    }


    for (let j = 0; j < time_string.length; j++)
    {
        let meetingTime = time_string[j].split(" "); //creates an array that contains[days_of_week, class_start_time, -, class_end_time]
        let days_of_week = meetingTime[0];


        while(days_of_week!="")
        {
            //adds both the start and end time for a particular class to a weekday
            if(days_of_week.includes("Mo"))
            {
                weekday_meeting_times[0].push(meetingTime[1]);
                weekday_meeting_times[0].push(meetingTime[3]);
                days_of_week = days_of_week.replace("Mo","");
            }
            if(days_of_week.includes("Tu"))
            {
                weekday_meeting_times[1].push(meetingTime[1]);
                weekday_meeting_times[1].push(meetingTime[3]);
                days_of_week = days_of_week.replace("Tu","");
            }
            if(days_of_week.includes("We"))
            {
                weekday_meeting_times[2].push(meetingTime[1]);
                weekday_meeting_times[2].push(meetingTime[3]);
                days_of_week = days_of_week.replace("We","");
            }
            if(days_of_week.includes("Th"))
            {
                weekday_meeting_times[3].push(meetingTime[1]);
                weekday_meeting_times[3].push(meetingTime[3]);
                days_of_week = days_of_week.replace("Th","");
            }
            if(days_of_week.includes("Fr"))
            {
                weekday_meeting_times[4].push(meetingTime[1]);
                weekday_meeting_times[4].push(meetingTime[3]);
                days_of_week = days_of_week.replace("Fr","");
            }
        }
    }
    return weekday_meeting_times;
}

function checkConflict(newTime, times) {
    // this method will return true if there is conflict with the list of times passed in anmd the newTime
    // TODO: implement this method

    return true;
}

function addTimeBlock(newTime, schedule) {
    // this method will add the time block to a schedule HTML element
    // TODO: implement this method, NOTE: there can be many ways to do, this is just a starter code

    return true;
}