/**
 * This file handles the recently viewed courses/instructors using localStorage
 * It replaces the server-side session storage with client-side storage
 */

document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a course page by looking for course code and title in the page
  saveCourseInfoIfPresent();
});

/**
 * Saves course information to localStorage if we're on a course or course-instructor page
 */
function saveCourseInfoIfPresent() {
  // Find course information in the page
  // This is adapting the session-based logic from browse.py and course_instructor views
  const courseCode = document.querySelector(
    'meta[name="course-code"]',
  )?.content;
  const courseTitle = document.querySelector(
    'meta[name="course-title"]',
  )?.content;

  if (!courseTitle) {
    return; // Not on a course or club page, or missing required data
  }

  // Get current URL
  const currentUrl = window.location.href;

  // Create the title in the same format as the server-side code

  let title = "";

  if (courseCode) {
    title += courseCode + " | ";
  }

  title += courseTitle;

  // Get existing history from localStorage
  let previousPaths = [];
  let previousPathsTitles = [];

  try {
    const savedPaths = localStorage.getItem("previous_paths");
    const savedTitles = localStorage.getItem("previous_paths_titles");

    if (savedPaths && savedTitles) {
      previousPaths = JSON.parse(savedPaths);
      previousPathsTitles = JSON.parse(savedTitles);
    }
  } catch (e) {
    console.error("Error loading history from localStorage:", e);
  }

  // Insert at beginning and remove duplicates
  // First check if the title already exists in the array
  const existingIndex = previousPathsTitles.indexOf(title);
  if (existingIndex !== -1) {
    // If the title exists, remove both the title and its corresponding path
    previousPathsTitles.splice(existingIndex, 1);
    previousPaths.splice(existingIndex, 1);
  }

  // Add the new path and title at the beginning
  previousPaths.unshift(currentUrl);
  previousPathsTitles.unshift(title);

  // Keep only the top 10 items
  if (previousPaths.length > 10) {
    previousPaths = previousPaths.slice(0, 10);
    previousPathsTitles = previousPathsTitles.slice(0, 10);
  }

  // Save back to localStorage
  localStorage.setItem("previous_paths", JSON.stringify(previousPaths));
  localStorage.setItem(
    "previous_paths_titles",
    JSON.stringify(previousPathsTitles),
  );

  // Also set cookies for compatibility with existing server-side code
  setCookie("previous_paths", JSON.stringify(previousPaths), 30);
  setCookie("previous_paths_titles", JSON.stringify(previousPathsTitles), 30);
}

/**
 * Helper function to set cookies
 */
function setCookie(name, value, days) {
  let expires = "";
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}
