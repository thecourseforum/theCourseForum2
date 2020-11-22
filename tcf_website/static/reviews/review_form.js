// Executed when DOM is ready
jQuery(function($) {
  // Fetch all subdepartment data from API
  var endpoint = 'http://localhost:8000/api/subdepartments/'
  $.getJSON(endpoint, function(data) {
      // Generate option tags
      var optionTags = $.map(data, function(subdept){
          return '<option value="' + subdept.id + '">' + subdept.mnemonic + '</option>'
      }).join('');
      // Prepend default option
      optionTags = '<option value="" disabled selected>[Select]</option>' + optionTags

      // Add option tags to select element in html
      $('#subject').html(optionTags)

      return this;
  });
});

function loadCourseData() {
  var subdeptID = $('#subject').val()
  console.log(subdeptID);

  // Fetch course data from API, based on selected subdepartment
  var pageSizeParam = '&page_size=1000'
  var endpoint = 'http://localhost:8000/api/courses/?subdepartment=' + subdeptID + pageSizeParam
  $.getJSON(endpoint, function(data) {
      console.log(data);
      // Generate option tags
      var optionTags = $.map(data.results, function(course){
          // 4-digit courseIDs only
          if(course.number > 1000)
              return '<option value="' + course.id + '">' + course.number + '</option>'
      }).join('');
      // Prepend default option
      optionTags = '<option value="" disabled selected>[Select]</option>' + optionTags

      // Add option tags to select element in html
      $('#courseID').html(optionTags)

      return this;
  });
}

function loadInstructorData() {
  var courseID = $('#courseID').val()
  console.log(courseID);

  // Fetch instructor data from API, based on selected course
  var pageSizeParam = '&page_size=1000'
  var endpoint = 'http://localhost:8000/api/instructors/?section__course=' + courseID + pageSizeParam
  $.getJSON(endpoint, function(data) {
      console.log(data);
      // Generate option tags
      var optionTags = $.map(data.results, function(instr){
          return '<option value="' + instr.id + '">' + instr.first_name +
                 ' ' + instr.last_name + '</option>'
      }).join('');
      // Prepend default option
      optionTags = '<option value="" disabled selected>[Select]</option>' + optionTags

      // Add option tags to select element in html
      $('#instructor').html(optionTags)

      return this;
  });
}
