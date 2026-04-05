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
});

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

    fetch(`${QA_URLS.questionDetail}${questionId}/`)
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
        })
        .catch(() => {
            contentArea.classList.remove('loading');
            contentArea.innerHTML = '<div class="no-post-selected"><p>Error loading question. Please try again.</p></div>';
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

                if (data.selected_question_id) {
                    url.searchParams.set('question', data.selected_question_id);
                }

                window.history.pushState({}, '', url);
            })
            .catch(() => {
                window.location.href = url.toString();
            });
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
    const searchInput = document.getElementById('courseFilterSearch');
    const itemsList = document.getElementById('courseFilterList');
    if (!searchInput || !itemsList) return;

    const dropdown = searchInput.closest('.dropdown');

    // Auto-focus search input when dropdown opens
    if (dropdown) {
        $(dropdown).on('shown.bs.dropdown', function () {
            searchInput.value = '';
            searchInput.focus();
            // Reset visibility
            itemsList.querySelectorAll('.dropdown-item').forEach(item => {
                item.classList.remove('d-none');
            });
        });
    }

    // Prevent dropdown from closing when clicking/typing in the search input
    searchInput.addEventListener('click', function (e) {
        e.stopPropagation();
    });

    // Filter items as user types
    searchInput.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        itemsList.querySelectorAll('.dropdown-item').forEach(item => {
            const text = item.textContent.trim().toLowerCase();
            if (!query || text === 'all courses' || text.includes(query)) {
                item.classList.remove('d-none');
            } else {
                item.classList.add('d-none');
            }
        });
    });
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
    const courseResults = document.getElementById('courseResults');
    const instructorSearchInput = document.getElementById('instructorSearch');
    const instructorIdInput = document.getElementById('instructorId');
    const instructorResults = document.getElementById('instructorResults');
    let instructorOptions = [];

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
                            courseResults.innerHTML = data.results.map(c =>
                                `<div class="course-result-item" data-id="${c.id}" data-code="${c.code}">
                                    <div class="course-result-code">${c.code}</div>
                                    <div class="course-result-title">${c.title}</div>
                                </div>`
                            ).join('');
                            courseResults.classList.add('show');

                            courseResults.querySelectorAll('.course-result-item').forEach(item => {
                                item.addEventListener('click', function () {
                                    courseIdInput.value = this.dataset.id;
                                    courseSearchInput.value = this.dataset.code;
                                    courseResults.classList.remove('show');
                                    resetInstructorSearch();
                                    loadInstructors(this.dataset.id);
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

    function loadInstructors(courseId) {
        if (!instructorSearchInput || !instructorResults) return;
        instructorSearchInput.disabled = true;
        instructorSearchInput.placeholder = 'Loading instructors...';
        instructorSearchInput.value = '';
        instructorResults.classList.remove('show');
        instructorResults.innerHTML = '<div class="course-result-item text-muted">Loading instructors...</div>';
        instructorResults.classList.add('show');

        fetch(`${QA_URLS.getInstructors}${courseId}/instructors/`)
            .then(r => r.json())
            .then(data => {
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
                instructorOptions = [];
                instructorSearchInput.disabled = false;
                instructorSearchInput.placeholder = 'Error loading instructors';
                instructorResults.innerHTML = '<div class="course-result-item text-muted">Error loading instructors</div>';
                instructorResults.classList.add('show');
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
            fetch(`/questions/${questionIdToDelete}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: deleteData,
            })
            .then(() => {
                $('#deleteQuestionModal').modal('hide');
                window.location.href = QA_URLS.dashboard;
            })
            .catch(err => {
                console.error('Delete question error:', err);
                $('#deleteQuestionModal').modal('hide');
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
            fetch(`/answers/${answerIdToDelete}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: deleteData,
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
                $('#deleteAnswerModal').modal('hide');
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
        // Remove duplicate listeners by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener('click', function () {
            if (!IS_AUTHENTICATED) {
                window.location.href = '/login/';
                return;
            }

            const type = this.dataset.type;   // 'question' or 'answer'
            const id = this.dataset.id;

            const url = type === 'question'
                ? `/questions/${id}/upvote/`
                : `/answers/${id}/upvote/`;
                
            const counterId = type === 'question'
                ? `question-vote-count-${id}`
                : `answer-vote-count-${id}`;

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    const container = this.closest('.post-actions');
                    const upBtn = container.querySelector('[data-action="up"]');
                    const counterEl = document.getElementById(counterId);

                    upBtn.classList.toggle('voted', data.user_vote === 1);
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
            .catch(err => console.error('Vote error:', err));
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
        .then(r => r.json())
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
                .then(() => {
                    // Reload the current question detail
                    const url = new URL(window.location);
                    const questionId = url.searchParams.get('question');
                    const activeItem = document.querySelector('.post-item.active');
                    const qId = questionId || (activeItem && activeItem.dataset.questionId);
                    if (qId) loadQuestionDetail(qId);
                })
                .catch(err => console.error('Answer submit error:', err))
                .finally(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Post Answer';
                    }
                });
            }
        })
        .catch(err => console.error('Duplicate check error:', err));
    });
}

// ─── Question Actions (Edit / Delete) ────────────────────────────────────────

function initQuestionActions() {
    const editModal = document.getElementById('editQuestionModal');

    document.querySelectorAll('.edit-question-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (!editModal) return;

            const qId = this.dataset.questionId;
            document.getElementById('editTitle').value = this.dataset.title || '';
            document.getElementById('editText').value = this.dataset.text || '';
            document.getElementById('editCourse').value = this.dataset.course || '';
            document.getElementById('editInstructor').value = this.dataset.instructor || '';
            document.getElementById('editQuestionForm').action = `${QA_URLS.editQuestion}${qId}/edit/`;

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
    if (closeEditBtn) closeEditBtn.addEventListener('click', closeEditModal);
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditModal);
    if (editModal) editModal.addEventListener('click', e => { if (e.target === editModal) closeEditModal(); });

    // Delete question button handler
    document.querySelectorAll('.delete-question-btn').forEach(btn => {
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
            document.getElementById('editAnswerForm').action = `${QA_URLS.editAnswer}${answerId}/edit/`;

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
    if (closeBtn) closeBtn.addEventListener('click', closeEditAnswerModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeEditAnswerModal);
    if (editAnswerModal) editAnswerModal.addEventListener('click', e => {
        if (e.target === editAnswerModal) closeEditAnswerModal();
    });

    document.querySelectorAll('.delete-answer-btn').forEach(btn => {
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
