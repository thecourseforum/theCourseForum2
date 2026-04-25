/**
 * Q&A Dashboard JavaScript
 * Handles all interactive functionality for the Q&A dashboard.
 */

document.addEventListener('DOMContentLoaded', function () {
    initQuestionSelection();
    initSearch();
    initCourseFilter();
    initNewPostModal();
    initDeleteQuestionModal();
    initDeleteAnswerModal();
    initVoting();
    initAnswerForm();
    initQuestionActions();
    initAnswerActions();
    initReplyForms();
    initTooltips();
});

function qaUrl(template, id) {
    return template.replace('__ID__', String(id));
}

function showRequestError(message) {
    window.alert(message);
}

// ─── Question Selection ───────────────────────────────────────────────────────

function initQuestionSelection() {
    document.querySelectorAll('.post-item').forEach(item => {
        item.addEventListener('click', function () {
            const questionId = this.dataset.questionId;
            loadQuestionDetail(questionId);

            document.querySelectorAll('.post-item').forEach(p => p.classList.remove('active'));
            this.classList.add('active');

            const url = new URL(window.location);
            url.searchParams.set('question', questionId);
            window.history.pushState({}, '', url);
        });
    });
}

function loadQuestionDetail(questionId) {
    const contentArea = document.getElementById('questionContent');
    contentArea.classList.add('loading');

    fetch(qaUrl(QA_URLS.questionDetail, questionId))
        .then(r => r.text())
        .then(html => {
            contentArea.innerHTML = html;
            contentArea.classList.remove('loading');
            // Re-initialise handlers for newly injected HTML
            initVoting();
            initAnswerForm();
            initQuestionActions();
            initAnswerActions();
            initReplyForms();
            initTooltips();
        })
        .catch(() => {
            contentArea.classList.remove('loading');
            contentArea.innerHTML = '<div class="no-post-selected"><p>Error loading question. Please try again.</p></div>';
        });
}

function refreshDashboard(url) {
    fetch(url.toString(), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
        .then(r => r.json())
        .then(data => {
            const postsList = document.getElementById('postsList');
            const contentArea = document.getElementById('questionContent');

            if (postsList) postsList.innerHTML = data.posts_html;
            if (contentArea) contentArea.innerHTML = data.detail_html;

            initQuestionSelection();
            initVoting();
            initAnswerForm();
            initQuestionActions();
            initAnswerActions();
            initReplyForms();
            initTooltips();

            if (data.selected_question_id) {
                url.searchParams.set('question', data.selected_question_id);
            }

            window.history.pushState({}, '', url);
        })
        .catch(() => {
            window.location.href = url.toString();
        });
}

// ─── Search ───────────────────────────────────────────────────────────────────

function initSearch() {
    const input = document.getElementById('searchInput');
    if (!input) return;

    let timeout;
    function runSearch() {
        const q = input.value.trim();
        const url = new URL(window.location);
        if (q) url.searchParams.set('q', q);
        else url.searchParams.delete('q');
        url.searchParams.delete('question');
        refreshDashboard(url);
    }

    input.addEventListener('input', function () {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            runSearch();
        }, 500);
    });

    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            clearTimeout(timeout);
            e.preventDefault();
            runSearch();
        }
    });
}

// ─── Course Filter ────────────────────────────────────────────────────────────

function initCourseFilter() {
    const departmentSearchInput = document.getElementById('departmentFilterSearch');
    const departmentItemsList = document.getElementById('departmentFilterList');
    const courseDropdownContainer = document.getElementById('courseDropdownContainer');
    const courseSearchInput = document.getElementById('courseFilterSearch');
    const courseItemsList = document.getElementById('courseFilterList');
    const departmentLabel = document.getElementById('departmentLabel');
    const courseLabel = document.getElementById('courseLabel');
    const departmentDropdownBtn = document.getElementById('departmentDropdown');
    const courseDropdownBtn = document.getElementById('courseDropdown');

    if (!departmentSearchInput || !departmentItemsList || !courseDropdownContainer || !courseSearchInput || !courseItemsList) return;

    // Get currently selected department from the page
    let selectedDepartmentId = '';
    const activeDeptItem = departmentItemsList.querySelector('.dropdown-item.active');
    if (activeDeptItem && activeDeptItem.dataset.departmentId) {
        selectedDepartmentId = activeDeptItem.dataset.departmentId;
    }

    let selectedCourseId = '';
    let selectedScope = '';
    const activeCourseItem = courseItemsList.querySelector('.dropdown-item.active');
    if (activeCourseItem && activeCourseItem.dataset.courseId) {
        selectedCourseId = activeCourseItem.dataset.courseId;
    }
    if (activeCourseItem && activeCourseItem.dataset.scope) {
        selectedScope = activeCourseItem.dataset.scope;
    }

    // Show course dropdown if a department is selected
    if (selectedDepartmentId) {
        setCourseDropdownVisible(true);
        filterCoursesByDepartment(selectedDepartmentId);
    } else {
        setCourseDropdownVisible(false);
    }

    updateFilterButtonStates();

    // ─── Department Dropdown Handling ───
    if (departmentDropdownBtn) {
        $(departmentDropdownBtn).closest('.dropdown').on('shown.bs.dropdown', function () {
            departmentSearchInput.value = '';
            departmentSearchInput.focus();
            departmentItemsList.querySelectorAll('.dropdown-item').forEach(item => {
                item.classList.remove('d-none');
            });
        });
    }

    departmentSearchInput.addEventListener('click', function (e) {
        e.stopPropagation();
    });

    departmentSearchInput.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        departmentItemsList.querySelectorAll('.dropdown-item').forEach(item => {
            const text = item.textContent.trim().toLowerCase();
            if (!query || text === 'all departments' || text.includes(query)) {
                item.classList.remove('d-none');
            } else {
                item.classList.add('d-none');
            }
        });
    });

    departmentItemsList.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function (e) {
            const deptId = this.dataset.departmentId;
            const deptText = this.textContent.trim();

            // Update department label
            if (departmentLabel) {
                departmentLabel.textContent = deptText === 'All Departments' ? 'All Departments' : deptText;
            }

            // Update active state
            departmentItemsList.querySelectorAll('.dropdown-item').forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            // Reset course dropdown and show/hide based on selection
            if (!deptId) {
                selectedDepartmentId = '';
                selectedCourseId = '';
                selectedScope = '';
                // All Departments selected
                setCourseDropdownVisible(false);
                if (courseLabel) courseLabel.textContent = 'All Posts';
                const url = new URL(window.location);
                url.searchParams.delete('department');
                url.searchParams.delete('course');
                url.searchParams.delete('scope');
                url.searchParams.delete('question');
                updateFilterButtonStates();
                refreshDashboard(url);
            } else {
                selectedDepartmentId = deptId;
                selectedCourseId = '';
                selectedScope = '';
                // Specific department selected - show course dropdown
                setCourseDropdownVisible(true);
                if (courseLabel) courseLabel.textContent = 'All Posts';

                // Filter and show courses for this department
                filterCoursesByDepartment(deptId);

                const url = new URL(window.location);
                url.searchParams.set('department', deptId);
                url.searchParams.delete('course');
                url.searchParams.delete('scope');
                url.searchParams.delete('question');
                updateFilterButtonStates();
                refreshDashboard(url);
            }

            e.preventDefault();
        });
    });

    // ─── Course Dropdown Handling ───
    if (courseDropdownBtn) {
        $(courseDropdownBtn).closest('.dropdown').on('shown.bs.dropdown', function () {
            courseSearchInput.value = '';
            courseSearchInput.focus();

            // Reapply current department filter whenever the menu opens.
            filterCoursesByDepartment(selectedDepartmentId);
        });
    }

    courseSearchInput.addEventListener('click', function (e) {
        e.stopPropagation();
    });

    courseSearchInput.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        filterCoursesByDepartment(selectedDepartmentId, query);
    });

    courseItemsList.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function (e) {
            const courseId = this.dataset.courseId;
            const scope = this.dataset.scope || '';
            const courseText = this.textContent.trim();

            // Update course label
            if (courseLabel) {
                courseLabel.textContent = courseText === 'All Posts' ? 'All Posts' : courseText;
            }

            // Navigate to the selected course
            if (courseId) {
                selectedCourseId = courseId;
                selectedScope = '';
                const url = new URL(window.location);
                if (selectedDepartmentId) {
                    url.searchParams.set('department', selectedDepartmentId);
                }
                url.searchParams.set('course', courseId);
                url.searchParams.delete('scope');
                url.searchParams.delete('question');
                updateFilterButtonStates();
                refreshDashboard(url);
            } else if (scope === 'department_broad') {
                selectedCourseId = '';
                selectedScope = 'department_broad';
                const url = new URL(window.location);
                if (selectedDepartmentId) {
                    url.searchParams.set('department', selectedDepartmentId);
                }
                url.searchParams.delete('course');
                url.searchParams.set('scope', 'department_broad');
                url.searchParams.delete('question');
                updateFilterButtonStates();
                refreshDashboard(url);
            } else {
                selectedCourseId = '';
                selectedScope = '';
                // All Posts selected
                const activeDeptItem = departmentItemsList.querySelector('.dropdown-item.active');
                const deptId = activeDeptItem ? activeDeptItem.dataset.departmentId : '';
                if (deptId) {
                    // Stay in the department but show all courses
                    const url = new URL(window.location);
                    url.searchParams.set('department', deptId);
                    url.searchParams.delete('course');
                    url.searchParams.delete('scope');
                    url.searchParams.delete('question');
                    updateFilterButtonStates();
                    refreshDashboard(url);
                } else {
                    // Shouldn't happen, but go back to all
                    const url = new URL(window.location);
                    url.searchParams.delete('department');
                    url.searchParams.delete('course');
                    url.searchParams.delete('scope');
                    url.searchParams.delete('question');
                    updateFilterButtonStates();
                    refreshDashboard(url);
                }
            }

            e.preventDefault();
        });
    });

    function filterCoursesByDepartment(departmentId, searchQuery = '') {
        const normalizedQuery = searchQuery.trim().toLowerCase();
        courseItemsList.querySelectorAll('.dropdown-item').forEach(item => {
            if (!item.dataset.courseId) {
                // "All Courses" option
                item.classList.remove('d-none');
            } else {
                const sameDepartment = !departmentId || item.dataset.departmentId === departmentId;
                const text = item.textContent.trim().toLowerCase();
                const matchesQuery = !normalizedQuery || text.includes(normalizedQuery);

                if (sameDepartment && matchesQuery) {
                    item.classList.remove('d-none');
                } else {
                    item.classList.add('d-none');
                }
            }
        });
        if (!searchQuery) {
            courseSearchInput.value = '';
        }
    }

    function setCourseDropdownVisible(isVisible) {
        if (isVisible) {
            courseDropdownContainer.style.display = 'block';
            requestAnimationFrame(() => {
                courseDropdownContainer.classList.add('is-visible');
            });
        } else {
            courseDropdownContainer.classList.remove('is-visible');
            window.setTimeout(() => {
                if (!courseDropdownContainer.classList.contains('is-visible')) {
                    courseDropdownContainer.style.display = 'none';
                }
            }, 200);
        }
    }

    function updateFilterButtonStates() {
        if (departmentDropdownBtn) {
            departmentDropdownBtn.classList.toggle('filter-active', Boolean(selectedDepartmentId));
        }
        if (courseDropdownBtn) {
            courseDropdownBtn.classList.toggle(
                'filter-active',
                Boolean(selectedCourseId || selectedScope)
            );
        }
    }
}

// ─── New Post Modal ───────────────────────────────────────────────────────────

function initNewPostModal() {
    const modal = document.getElementById('newPostModal');
    if (!modal) return;

    const openBtn = document.getElementById('openNewPostModal');
    const closeBtn = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelModal');
    const form = document.getElementById('newPostForm');
    const courseSearchInput = document.getElementById('courseSearch');
    const courseIdInput = document.getElementById('courseId');
    const departmentIdInput = document.getElementById('departmentId');
    const courseResults = document.getElementById('courseResults');
    const instructorSearchInput = document.getElementById('instructorSearch');
    const instructorIdInput = document.getElementById('instructorId');
    const instructorResults = document.getElementById('instructorResults');
    let instructorOptions = [];
    let selectedTargetType = 'none';
    let instructorRequestToken = 0;

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function resetInstructorSearch() {
        instructorOptions = [];
        if (instructorIdInput) instructorIdInput.value = '';
        if (instructorSearchInput) {
            instructorSearchInput.value = '';
            instructorSearchInput.disabled = true;
            instructorSearchInput.placeholder = 'Select a course first...';
        }
        if (instructorResults) {
            instructorResults.classList.remove('show');
            instructorResults.innerHTML = '';
        }
    }

    function setDepartmentMode() {
        selectedTargetType = 'department';
        // Invalidate any in-flight instructor request from previous course selection.
        instructorRequestToken += 1;
        if (instructorIdInput) instructorIdInput.value = '';
        if (instructorSearchInput) {
            instructorSearchInput.value = '';
            instructorSearchInput.disabled = true;
            instructorSearchInput.placeholder = 'Instructor not required for department posts';
        }
        if (instructorResults) {
            instructorResults.classList.remove('show');
            instructorResults.innerHTML = '';
        }
    }

    function renderInstructorResults(query = '') {
        if (!instructorResults || !instructorSearchInput) return;

        const normalizedQuery = query.trim().toLowerCase();
        const filteredOptions = instructorOptions.filter(instructor =>
            instructor.name.toLowerCase().includes(normalizedQuery)
        );

        if (filteredOptions.length === 0) {
            instructorResults.innerHTML = '<div class="course-result-item text-muted">No instructors found</div>';
            instructorResults.classList.add('show');
            return;
        }

        instructorResults.innerHTML = filteredOptions.map(instructor =>
            `<div class="course-result-item" data-id="${instructor.id}" data-name="${escapeHtml(instructor.name)}">
                <div class="course-result-code">${escapeHtml(instructor.name)}</div>
            </div>`
        ).join('');
        instructorResults.classList.add('show');

        instructorResults.querySelectorAll('.course-result-item').forEach(item => {
            item.addEventListener('click', function () {
                if (instructorIdInput) instructorIdInput.value = this.dataset.id;
                instructorSearchInput.value = this.dataset.name;
                instructorResults.classList.remove('show');
            });
        });
    }

    function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        if (form) form.reset();
        if (courseIdInput) courseIdInput.value = '';
        if (departmentIdInput) departmentIdInput.value = '';
        selectedTargetType = 'none';
        instructorRequestToken += 1;
        if (courseResults) courseResults.classList.remove('show');
        resetInstructorSearch();
    }

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    // Course search autocomplete
    if (courseSearchInput) {
        let searchTimeout;
        courseSearchInput.addEventListener('input', function () {
            if (courseIdInput) courseIdInput.value = '';
            if (departmentIdInput) departmentIdInput.value = '';
            selectedTargetType = 'none';
            instructorRequestToken += 1;
            resetInstructorSearch();
            clearTimeout(searchTimeout);
            const q = this.value.trim();
            if (q.length < 2) {
                courseResults.classList.remove('show');
                return;
            }
            searchTimeout = setTimeout(() => {
                fetch(`${QA_URLS.searchCourses}?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            courseResults.innerHTML = data.results.map(c => {
                                const id = escapeHtml(c.id);
                                const code = escapeHtml(c.code);
                                const type = escapeHtml(c.type);
                                const title = escapeHtml(c.title);
                                return `<div class="course-result-item" data-id="${id}" data-code="${code}" data-type="${type}">
                                    <div class="course-result-code">${code}</div>
                                    <div class="course-result-title">${title}</div>
                                </div>`
                            }).join('');
                            courseResults.classList.add('show');

                            courseResults.querySelectorAll('.course-result-item').forEach(item => {
                                item.addEventListener('click', function () {
                                    courseSearchInput.value = this.dataset.code;
                                    courseResults.classList.remove('show');
                                    if (this.dataset.type === 'course') {
                                        selectedTargetType = 'course';
                                        courseIdInput.value = this.dataset.id;
                                        if (departmentIdInput) departmentIdInput.value = '';
                                        resetInstructorSearch();
                                        const requestToken = ++instructorRequestToken;
                                        loadInstructors(this.dataset.id, requestToken);
                                    } else {
                                        if (courseIdInput) courseIdInput.value = '';
                                        if (departmentIdInput) departmentIdInput.value = this.dataset.id;
                                        setDepartmentMode();
                                    }
                                });
                            });
                        } else {
                            courseResults.innerHTML = '<div class="course-result-item text-muted">No courses found</div>';
                            courseResults.classList.add('show');
                        }
                    });
            }, 300);
        });

        courseSearchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && courseIdInput.value) {
                courseIdInput.value = '';
                selectedTargetType = 'none';
                instructorRequestToken += 1;
                resetInstructorSearch();
            }
            if (e.key === 'Backspace' && departmentIdInput && departmentIdInput.value) {
                departmentIdInput.value = '';
                selectedTargetType = 'none';
                instructorRequestToken += 1;
                resetInstructorSearch();
            }
        });

        document.addEventListener('click', function (e) {
            if (!courseSearchInput.contains(e.target) && !courseResults.contains(e.target)) {
                courseResults.classList.remove('show');
            }
        });
    }

    if (instructorSearchInput && instructorResults) {
        instructorSearchInput.addEventListener('click', function (e) {
            e.stopPropagation();
            if (!this.disabled) {
                renderInstructorResults(this.value);
            }
        });

        instructorSearchInput.addEventListener('input', function () {
            if (instructorIdInput) instructorIdInput.value = '';
            if (this.disabled) return;
            renderInstructorResults(this.value);
        });

        document.addEventListener('click', function (e) {
            if (!instructorSearchInput.contains(e.target) && !instructorResults.contains(e.target)) {
                instructorResults.classList.remove('show');
            }
        });
    }

    function loadInstructors(courseId, requestToken) {
        if (!instructorSearchInput || !instructorResults) return;
        instructorSearchInput.disabled = true;
        instructorSearchInput.placeholder = 'Loading instructors...';
        instructorSearchInput.value = '';
        instructorResults.classList.remove('show');
        instructorResults.innerHTML = '<div class="course-result-item text-muted">Loading instructors...</div>';
        instructorResults.classList.add('show');

        fetch(qaUrl(QA_URLS.getInstructors, courseId))
            .then(r => r.json())
            .then(data => {
                if (requestToken !== instructorRequestToken || selectedTargetType !== 'course') {
                    return;
                }
                instructorOptions = data.instructors || [];
                instructorSearchInput.disabled = false;
                instructorSearchInput.placeholder = instructorOptions.length > 0 ? 'Search instructors...' : 'No instructors found';
                instructorSearchInput.focus();

                if (instructorOptions.length > 0) {
                    renderInstructorResults('');
                } else {
                    instructorResults.innerHTML = '<div class="course-result-item text-muted">No instructors found</div>';
                    instructorResults.classList.add('show');
                }
            })
            .catch(() => {
                if (requestToken !== instructorRequestToken || selectedTargetType !== 'course') {
                    return;
                }
                instructorOptions = [];
                instructorSearchInput.disabled = false;
                instructorSearchInput.placeholder = 'Error loading instructors';
                instructorResults.innerHTML = '<div class="course-result-item text-muted">Error loading instructors</div>';
                instructorResults.classList.add('show');
            });
    }

    if (form) {
        form.addEventListener('submit', function (e) {
            const hasCourse = courseIdInput && courseIdInput.value;
            const hasDepartment = departmentIdInput && departmentIdInput.value;

            if (!hasCourse && !hasDepartment) {
                e.preventDefault();
                courseSearchInput.focus();
                courseSearchInput.setCustomValidity('Please select a course or a department.');
                courseSearchInput.reportValidity();
                return;
            }

            courseSearchInput.setCustomValidity('');

            if (hasDepartment && instructorIdInput) {
                instructorIdInput.value = '';
            }
            if (hasDepartment && courseIdInput) {
                courseIdInput.value = '';
            }
        });
    }
}

// ─── Delete Question Modal ────────────────────────────────────────────────────

let questionIdToDelete = null;

function initDeleteQuestionModal() {
    const confirmDeleteBtn = document.getElementById('confirmDeleteQuestion');

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function () {
            if (!questionIdToDelete) return;

            const deleteData = new FormData();
            deleteData.append('csrfmiddlewaretoken', CSRF_TOKEN);
            fetch(qaUrl(QA_URLS.deleteQuestion, questionIdToDelete), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: deleteData,
            })
            .then(r => {
                if (!r.ok) throw new Error(r.status);
                return r;
            })
            .then(() => {
                $('#deleteQuestionModal').modal('hide');
                window.location.href = QA_URLS.dashboard;
            })
            .catch(err => {
                console.error('Delete question error:', err);
                showRequestError('Unable to delete the question right now. Please try again.');
            });
        });
    }
}

function openDeleteQuestionModal(qId) {
    questionIdToDelete = qId;
    $('#deleteQuestionModal').modal('show');
}

// ─── Delete Answer Modal ──────────────────────────────────────────────────────

let answerIdToDelete = null;

function initDeleteAnswerModal() {
    const confirmDeleteBtn = document.getElementById('confirmDeleteAnswer');

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function () {
            if (!answerIdToDelete) return;

            const deleteData = new FormData();
            deleteData.append('csrfmiddlewaretoken', CSRF_TOKEN);
            fetch(qaUrl(QA_URLS.deleteAnswer, answerIdToDelete), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: deleteData,
            })
            .then(r => {
                if (!r.ok) throw new Error(r.status);
                return r;
            })
            .then(() => {
                $('#deleteAnswerModal').modal('hide');
                const url = new URL(window.location);
                const qId = url.searchParams.get('question');
                const activeItem = document.querySelector('.post-item.active');
                const questionId = qId || (activeItem && activeItem.dataset.questionId);
                if (questionId) loadQuestionDetail(questionId);
            })
            .catch(err => {
                console.error('Delete answer error:', err);
                showRequestError('Unable to delete the answer right now. Please try again.');
            });
        });
    }
}

function openDeleteAnswerModal(aId) {
    answerIdToDelete = aId;
    $('#deleteAnswerModal').modal('show');
}

// ─── Voting ───────────────────────────────────────────────────────────────────

function initVoting() {
    document.querySelectorAll('.vote-btn').forEach(btn => {
        if (btn.dataset.votingBound === 'true') return;
        btn.dataset.votingBound = 'true';

        btn.addEventListener('click', function () {
            if (!IS_AUTHENTICATED) {
                window.location.href = '/login/';
                return;
            }

            const type = this.dataset.type;   // 'question' or 'answer'
            const id = this.dataset.id;

            const url = type === 'question'
                ? qaUrl(QA_URLS.upvoteQuestion, id)
                : qaUrl(QA_URLS.upvoteAnswer, id);
                
            const counterId = type === 'question'
                ? `question-vote-count-${id}`
                : `answer-vote-count-${id}`;

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
            })
            .then(r => {
                if (!r.ok) throw new Error(r.status);
                return r.json();
            })
            .then(data => {
                if (data.ok) {
                    const container = this.closest('.post-actions');
                    const upBtn = container
                        ? container.querySelector('[data-action="up"]')
                        : this;
                    const counterEl = document.getElementById(counterId);

                    if (upBtn) upBtn.classList.toggle('voted', data.user_vote === 1);
                    if (counterEl) counterEl.textContent = data.votes;

                    // Keep sidebar list in sync for question votes
                    if (type === 'question') {
                        const sidebarContainer = document.querySelector(`#sidebar-vote-count-${id}`);
                        if (sidebarContainer) {
                            const sidebarNum = sidebarContainer.querySelector('.sidebar-vote-num');
                            if(sidebarNum) sidebarNum.textContent = data.votes;
                            sidebarContainer.classList.toggle('voted', data.user_vote === 1)
                        }
                    }
                }
            })
            .catch(err => {
                console.error('Vote error:', err);
                showRequestError('Unable to record your vote right now. Please try again.');
            });
        });
    });
}

// ─── Answer Form ──────────────────────────────────────────────────────────────

function initAnswerForm() {
    const form = document.getElementById('mainAnswerForm');
    if (!form) return;

    const newForm = form.cloneNode(true);
    form.parentNode.replaceChild(newForm, form);

    newForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const warning = document.getElementById('duplicate-answer-warning');
        if (warning) warning.style.display = 'none';

        const formData = new FormData(newForm);
        const submitBtn = newForm.querySelector('.btn-submit-reply');

        // Check for duplicates first
        fetch('/answers/check_duplicate/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => {
            if (!r.ok) throw new Error(r.status);
            return r.json();
        })
        .then(data => {
            if (data.duplicate) {
                if (warning) warning.style.display = 'inline';
            } else {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Posting...';
                }

                fetch(newForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                })
                .then(r => {
                    if (!r.ok) throw new Error(r.status);
                    return r;
                })
                .then(() => {
                    incrementAnswerCount();
                    // Reload the current question detail
                    const url = new URL(window.location);
                    const questionId = url.searchParams.get('question');
                    const activeItem = document.querySelector('.post-item.active');
                    const qId = questionId || (activeItem && activeItem.dataset.questionId);
                    if (qId) loadQuestionDetail(qId);
                })
                .catch(err => {
                    console.error('Answer submit error:', err);
                    showRequestError('Unable to post your answer right now. Please try again.');
                })
                .finally(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Post Answer';
                    }
                });
            }
        })
        .catch(err => {
            console.error('Duplicate check error:', err);
            showRequestError('Unable to validate your answer right now. Please try again.');
        });
    });
}

function incrementAnswerCount() {
    const counter = document.querySelector('.response-count');
    if (!counter) return;

    const match = counter.textContent.match(/\d+/);
    if (!match) return;

    counter.textContent = `(${parseInt(match[0], 10) + 1})`;
}

function initTooltips() {
    if (typeof $ !== 'function') return;
    $('[data-toggle="tooltip"]').tooltip();
}

// ─── Question Actions (Edit / Delete) ────────────────────────────────────────

function initQuestionActions() {
    const editModal = document.getElementById('editQuestionModal');

    document.querySelectorAll('.edit-question-btn').forEach(btn => {
        if (btn.dataset.questionActionBound === 'true') return;
        btn.dataset.questionActionBound = 'true';
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (!editModal) return;

            const qId = this.dataset.questionId;
            document.getElementById('editTitle').value = this.dataset.title || '';
            document.getElementById('editText').value = this.dataset.text || '';
            document.getElementById('editCourse').value = this.dataset.course || '';
            document.getElementById('editDepartment').value = this.dataset.department || '';
            document.getElementById('editInstructor').value = this.dataset.instructor || '';
            document.getElementById('editQuestionForm').action = qaUrl(QA_URLS.editQuestion, qId);

            editModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });

    const closeEditBtn = document.getElementById('closeEditModal');
    const cancelEditBtn = document.getElementById('cancelEditModal');
    function closeEditModal() {
        if (editModal) {
            editModal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    if (closeEditBtn && closeEditBtn.dataset.modalBound !== 'true') {
        closeEditBtn.dataset.modalBound = 'true';
        closeEditBtn.addEventListener('click', closeEditModal);
    }
    if (cancelEditBtn && cancelEditBtn.dataset.modalBound !== 'true') {
        cancelEditBtn.dataset.modalBound = 'true';
        cancelEditBtn.addEventListener('click', closeEditModal);
    }
    if (editModal && editModal.dataset.modalBound !== 'true') {
        editModal.dataset.modalBound = 'true';
        editModal.addEventListener('click', e => { if (e.target === editModal) closeEditModal(); });
    }

    // Delete question button handler
    document.querySelectorAll('.delete-question-btn').forEach(btn => {
        if (btn.dataset.deleteQuestionBound === 'true') return;
        btn.dataset.deleteQuestionBound = 'true';
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const qId = this.dataset.questionId;
            openDeleteQuestionModal(qId);
        });
    });
}

// ─── Answer Actions (Edit / Delete) ──────────────────────────────────────────

function initAnswerActions() {
    const editAnswerModal = document.getElementById('editAnswerModal');

    document.querySelectorAll('.edit-answer-btn').forEach(btn => {
        if (btn.dataset.answerActionBound === 'true') return;
        btn.dataset.answerActionBound = 'true';
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (!editAnswerModal) return;

            const answerId = this.dataset.answerId;
            document.getElementById('editAnswerText').value = this.dataset.text || '';
            const semSelect = document.getElementById('editAnswerSemester');
            if (semSelect && this.dataset.semester) semSelect.value = this.dataset.semester;
            const mainForm = document.getElementById('mainAnswerForm');
            const questionId = mainForm ? mainForm.querySelector('[name="question"]').value : '';
            document.getElementById('editAnswerQuestion').value = questionId;
            document.getElementById('editAnswerForm').action = qaUrl(QA_URLS.editAnswer, answerId);

            editAnswerModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });

    function closeEditAnswerModal() {
        if (editAnswerModal) {
            editAnswerModal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    const closeBtn = document.getElementById('closeEditAnswerModal');
    const cancelBtn = document.getElementById('cancelEditAnswerModal');
    if (closeBtn && closeBtn.dataset.modalBound !== 'true') {
        closeBtn.dataset.modalBound = 'true';
        closeBtn.addEventListener('click', closeEditAnswerModal);
    }
    if (cancelBtn && cancelBtn.dataset.modalBound !== 'true') {
        cancelBtn.dataset.modalBound = 'true';
        cancelBtn.addEventListener('click', closeEditAnswerModal);
    }
    if (editAnswerModal && editAnswerModal.dataset.modalBound !== 'true') {
        editAnswerModal.dataset.modalBound = 'true';
        editAnswerModal.addEventListener('click', e => {
            if (e.target === editAnswerModal) closeEditAnswerModal();
        });
    }

    document.querySelectorAll('.delete-answer-btn').forEach(btn => {
        if (btn.dataset.deleteAnswerBound === 'true') return;
        btn.dataset.deleteAnswerBound = 'true';
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const answerId = this.dataset.answerId;
            openDeleteAnswerModal(answerId);
        });
    });
}

// ─── Reply Forms ──────────────────────────────────────────────────────────────

function initReplyForms() {
    // Handle Reply button clicks
    document.querySelectorAll('.reply-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const answerId = this.dataset.answerId;
            const replyForm = document.getElementById(`reply-form-${answerId}`);

            // Hide all other reply forms
            document.querySelectorAll('.reply-form-container').forEach(form => {
                if (form.id !== `reply-form-${answerId}`) {
                    form.style.display = 'none';
                }
            });

            // Toggle this reply form
            if (replyForm) {
                replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            }
        });
    });

    // Handle Cancel button clicks
    document.querySelectorAll('.btn-cancel-reply').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const replyForm = this.closest('.reply-form-container');
            if (replyForm) {
                replyForm.style.display = 'none';
                // Clear the form
                const form = replyForm.querySelector('form');
                if (form) {
                    form.querySelector('textarea').value = '';
                    form.querySelector('select').selectedIndex = 0;
                }
            }
        });
    });
}
