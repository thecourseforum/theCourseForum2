/**
 * Review form cascade: inline course/club pick without full reload, then
 * term → instructor (courses) via XHR. Relies on URLs from the form data-* attrs.
 */
(function () {
  const form = document.getElementById("reviewForm");
  if (!form || form.dataset.reviewCascade !== "1") {
    return;
  }

  const isClub = form.dataset.isClub === "true";
  const semestersUrl = form.dataset.semestersUrl;
  const instructorsUrl = form.dataset.instructorsUrl;

  const courseHidden = document.getElementById("review-course-id");
  const clubHidden = document.getElementById("review-club-id");
  const semesterSelect = document.getElementById("semester");
  const instructorSelect = document.getElementById("instructor");
  const instructorError = document.getElementById(
    "review-instructor-fetch-error",
  );
  const mainFieldset = document.getElementById("review-main-fieldset");
  const submitBtn = document.getElementById("submitBtn");
  const courseHeading = document.getElementById("review-course-heading");
  const clubHeading = document.getElementById("review-club-heading");
  const courseHint = document.getElementById("review-course-hint");
  const clubHint = document.getElementById("review-club-hint");
  const logisticsSection = document.getElementById("review-logistics-section");

  async function fetchJson(url) {
    const res = await fetch(url, {
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    const text = await res.text();
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    try {
      return JSON.parse(text);
    } catch {
      throw new Error("Expected JSON from server");
    }
  }

  function setSectionLocked(sectionEl, locked) {
    if (!sectionEl) return;
    sectionEl.classList.toggle("review-cascade--locked", locked);
  }

  function setMainEnabled(on) {
    if (!mainFieldset) return;
    mainFieldset.disabled = !on;
    if (submitBtn) submitBtn.disabled = !on;
    setSectionLocked(document.getElementById("review-body-section"), !on);
    setSectionLocked(document.getElementById("review-ratings-section"), !on);
    setSectionLocked(document.getElementById("review-workload-section"), !on);
  }

  function resetInstructorOptions() {
    if (!instructorSelect) return;
    instructorSelect.innerHTML = '<option value="">Select instructor…</option>';
    instructorSelect.disabled = true;
    instructorSelect.required = false;
    if (instructorError) {
      instructorError.textContent = "";
      instructorError.hidden = true;
    }
  }

  function coursePicked(courseId, codeText, titleText) {
    if (courseHidden) {
      courseHidden.value = courseId;
      courseHidden.removeAttribute("disabled");
    }
    if (courseHeading) {
      courseHeading.textContent =
        codeText && titleText
          ? `${codeText} — ${titleText}`
          : codeText || "Course";
    }
    if (courseHint) {
      courseHint.textContent = "Need a different class? Search again below.";
    }
    if (semesterSelect) {
      semesterSelect.disabled = false;
      semesterSelect.required = true;
    }
    setSectionLocked(logisticsSection, false);
    resetInstructorOptions();
    setMainEnabled(false);
    loadSemestersForCourse(courseId);
  }

  function clubPicked(clubId, nameText, categoryText) {
    if (clubHidden) {
      clubHidden.value = clubId;
      clubHidden.removeAttribute("disabled");
    }
    if (clubHeading) {
      clubHeading.textContent =
        nameText && categoryText
          ? `${nameText} — ${categoryText}`
          : nameText || "Club";
    }
    if (clubHint) {
      clubHint.textContent = "Pick another club? Search again below.";
    }
    const clubSemEl = document.getElementById("review-club-semesters-data");
    if (clubSemEl && semesterSelect) {
      const rows = JSON.parse(clubSemEl.textContent);
      semesterSelect.innerHTML = "";
      const ph = document.createElement("option");
      ph.value = "";
      ph.disabled = true;
      ph.selected = true;
      ph.textContent = "Select term…";
      semesterSelect.appendChild(ph);
      for (const row of rows) {
        const o = document.createElement("option");
        o.value = String(row.id);
        o.textContent = row.label;
        semesterSelect.appendChild(o);
      }
    }
    if (semesterSelect) {
      semesterSelect.disabled = false;
      semesterSelect.required = true;
    }
    setSectionLocked(logisticsSection, false);
    setMainEnabled(false);
    onSemesterChange();
  }

  async function loadSemestersForCourse(courseId) {
    if (!semesterSelect || !semestersUrl) return;
    semesterSelect.innerHTML = "";
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.disabled = true;
    opt0.selected = true;
    opt0.textContent = "Loading terms…";
    semesterSelect.appendChild(opt0);
    semesterSelect.disabled = true;

    try {
      const url = new URL(semestersUrl, window.location.origin);
      url.searchParams.set("course", courseId);
      const data = await fetchJson(url.toString());
      semesterSelect.innerHTML = "";
      const ph = document.createElement("option");
      ph.value = "";
      ph.disabled = true;
      ph.selected = true;
      ph.textContent = "Select term…";
      semesterSelect.appendChild(ph);
      for (const row of data.semesters || []) {
        const o = document.createElement("option");
        o.value = String(row.id);
        o.textContent = row.label;
        semesterSelect.appendChild(o);
      }
      semesterSelect.disabled = false;
    } catch {
      semesterSelect.innerHTML = "";
      const err = document.createElement("option");
      err.value = "";
      err.textContent = "Could not load terms";
      semesterSelect.appendChild(err);
      semesterSelect.disabled = true;
    }
  }

  async function loadInstructors(courseId, semesterId) {
    if (!instructorSelect || !instructorsUrl) return;
    instructorSelect.disabled = true;
    instructorSelect.innerHTML = '<option value="">Loading…</option>';
    if (instructorError) {
      instructorError.textContent = "";
      instructorError.hidden = true;
    }

    try {
      const url = new URL(instructorsUrl, window.location.origin);
      url.searchParams.set("course", courseId);
      url.searchParams.set("semester", semesterId);
      const data = await fetchJson(url.toString());
      instructorSelect.innerHTML =
        '<option value="">Select instructor…</option>';
      for (const row of data.instructors || []) {
        const o = document.createElement("option");
        o.value = String(row.id);
        o.textContent = `${row.last_name}, ${row.first_name}`;
        instructorSelect.appendChild(o);
      }
      instructorSelect.disabled = false;
      instructorSelect.required = true;
    } catch {
      instructorSelect.innerHTML =
        '<option value="">Select instructor…</option>';
      instructorSelect.disabled = true;
      if (instructorError) {
        instructorError.textContent =
          "Could not load instructors. Try another term.";
        instructorError.hidden = false;
      }
    }
  }

  function onSemesterChange() {
    if (isClub) {
      const sid = semesterSelect && semesterSelect.value;
      setMainEnabled(Boolean(sid));
      return;
    }
    const sid = semesterSelect && semesterSelect.value;
    const cid = courseHidden && courseHidden.value;
    resetInstructorOptions();
    setMainEnabled(false);
    if (sid && cid) {
      loadInstructors(cid, sid);
    }
  }

  function onInstructorChange() {
    if (isClub) return;
    const iid = instructorSelect && instructorSelect.value;
    setMainEnabled(Boolean(iid));
  }

  document.body.addEventListener("click", function (ev) {
    const courseLink = ev.target.closest(
      "#review-course-picker .autocomplete-item__link",
    );
    if (courseLink) {
      const u = new URL(courseLink.href, window.location.origin);
      const cid = u.searchParams.get("course");
      if (!cid) return;
      ev.preventDefault();
      const codeEl = courseLink.querySelector(".autocomplete-item__code");
      const titleEl = courseLink.querySelector(".autocomplete-item__title");
      coursePicked(
        cid,
        codeEl ? codeEl.textContent.trim() : "",
        titleEl ? titleEl.textContent.trim() : "",
      );
      const dd = courseLink.closest(".autocomplete-dropdown-container");
      if (dd) {
        dd.style.display = "none";
        dd.innerHTML = "";
      }
      const input = document.querySelector(
        "#review-course-picker input[name=q]",
      );
      if (input) input.value = "";
      return;
    }

    const clubLink = ev.target.closest(
      "#review-club-picker .autocomplete-item__link",
    );
    if (clubLink) {
      const u = new URL(clubLink.href, window.location.origin);
      const bid = u.searchParams.get("club");
      if (!bid) return;
      ev.preventDefault();
      const titleEl = clubLink.querySelector(".autocomplete-item__title");
      clubPicked(bid, titleEl ? titleEl.textContent.trim() : "", "");
      const dd = clubLink.closest(".autocomplete-dropdown-container");
      if (dd) {
        dd.style.display = "none";
        dd.innerHTML = "";
      }
      const input = document.querySelector("#review-club-picker input[name=q]");
      if (input) input.value = "";
    }
  });

  if (semesterSelect) {
    semesterSelect.addEventListener("change", onSemesterChange);
  }
  if (instructorSelect) {
    instructorSelect.addEventListener("change", onInstructorChange);
  }

  // Initial sync (SSR deep links and error re-renders)
  if (isClub) {
    const hasClub = clubHidden && clubHidden.value && !clubHidden.disabled;
    if (semesterSelect) {
      semesterSelect.disabled = !hasClub;
      semesterSelect.required = hasClub;
    }
    setSectionLocked(logisticsSection, !hasClub);
    const sid = semesterSelect && semesterSelect.value;
    setMainEnabled(hasClub && Boolean(sid));
  } else {
    const hasCourse =
      courseHidden && courseHidden.value && !courseHidden.disabled;
    if (semesterSelect) {
      semesterSelect.disabled = !hasCourse;
      semesterSelect.required = hasCourse;
    }
    setSectionLocked(logisticsSection, !hasCourse);
    const iid = instructorSelect && instructorSelect.value;
    setMainEnabled(hasCourse && Boolean(semesterSelect.value) && Boolean(iid));
  }

  if (form.dataset.mainUnlocked === "1") {
    setMainEnabled(true);
  }
})();
