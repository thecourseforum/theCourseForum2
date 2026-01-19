/**
 * Forum Dashboard JavaScript
 * Handles all interactive functionality for the Q&A forum
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initPostSelection();
    initSearch();
    initNewPostModal();
    initReplyModal();
    initVoting();
    initResponseForm();
    initCourseSearch();
    initPostActions();
    initResponseActions();
});

/**
 * Post Selection - Click on posts in sidebar to view details
 */
function initPostSelection() {
    const postItems = document.querySelectorAll('.post-item');
    
    postItems.forEach(item => {
        item.addEventListener('click', function() {
            const postId = this.dataset.postId;
            loadPostDetail(postId);
            
            // Update active state
            document.querySelectorAll('.post-item').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            
            // Update URL without reload
            const url = new URL(window.location);
            url.searchParams.set('post', postId);
            window.history.pushState({}, '', url);
        });
    });
}

/**
 * Load post detail via AJAX
 */
function loadPostDetail(postId) {
    const contentArea = document.getElementById('postContent');
    contentArea.classList.add('loading');
    
    fetch(`${FORUM_URLS.postDetail}${postId}/`)
        .then(response => response.text())
        .then(html => {
            contentArea.innerHTML = html;
            contentArea.classList.remove('loading');
            
            // Reinitialize event handlers for the new content
            initVoting();
            initResponseForm();
            initPostActions();
            initResponseActions();
            initReplyModal();
        })
        .catch(error => {
            console.error('Error loading post:', error);
            contentArea.classList.remove('loading');
            contentArea.innerHTML = '<div class="no-post-selected"><p>Error loading post. Please try again.</p></div>';
        });
}

/**
 * Search functionality
 */
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        searchTimeout = setTimeout(() => {
            const url = new URL(window.location);
            if (query) {
                url.searchParams.set('q', query);
            } else {
                url.searchParams.delete('q');
            }
            url.searchParams.delete('post'); // Clear selected post on new search
            window.location.href = url.toString();
        }, 500);
    });
    
    // Handle Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            clearTimeout(searchTimeout);
            const url = new URL(window.location);
            const query = this.value.trim();
            if (query) {
                url.searchParams.set('q', query);
            } else {
                url.searchParams.delete('q');
            }
            url.searchParams.delete('post');
            window.location.href = url.toString();
        }
    });
}

/**
 * New Post Modal
 */
function initNewPostModal() {
    const modal = document.getElementById('newPostModal');
    const openBtn = document.getElementById('openNewPostModal');
    const openBtnEmpty = document.getElementById('openNewPostModalEmpty');
    const closeBtn = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelModal');
    const form = document.getElementById('newPostForm');
    
    if (!modal) return;
    
    function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        form.reset();
        // Clear course selection
        const courseIdEl = document.getElementById('courseId');
        if (courseIdEl) courseIdEl.value = '';
        const courseSearch = document.getElementById('courseSearch');
        if (courseSearch) courseSearch.value = '';
        const results = document.getElementById('courseResults');
        if (results) results.classList.remove('show');
    }
    
    if (openBtn) openBtn.addEventListener('click', openModal);
    if (openBtnEmpty) openBtnEmpty.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    
    // Close on overlay click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) closeModal();
    });
    
    // Form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const submitBtn = form.querySelector('.btn-submit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            
            fetch(FORUM_URLS.createPost, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    closeModal();
                    // Redirect to the new post
                    window.location.href = `${FORUM_URLS.dashboard}?post=${data.post_id}`;
                } else {
                    alert('Error creating post: ' + JSON.stringify(data.errors));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating post. Please try again.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Post';
            });
        });
    }
}

/**
 * Reply Modal (for nested replies)
 */
function initReplyModal() {
    const modal = document.getElementById('replyModal');
    if (!modal) return;
    
    const closeBtn = document.getElementById('closeReplyModal');
    const cancelBtn = document.getElementById('cancelReplyModal');
    const form = document.getElementById('replyForm');
    
    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        if (form) form.reset();
    }
    
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) closeModal();
    });
    
    // Reply buttons
    document.querySelectorAll('.reply-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const responseId = this.dataset.responseId;
            const postId = this.dataset.postId;
            
            document.getElementById('replyParentId').value = responseId;
            document.getElementById('replyPostId').value = postId;
            
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });
    
    // Form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const postId = document.getElementById('replyPostId').value;
            const formData = new FormData(form);
            const submitBtn = form.querySelector('.btn-submit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Posting...';
            
            fetch(`${FORUM_URLS.createResponse}${postId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    closeModal();
                    // Reload the post detail to show new response
                    loadPostDetail(postId);
                } else {
                    alert('Error posting reply: ' + JSON.stringify(data.errors));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error posting reply. Please try again.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Post Reply';
            });
        });
    }
}

/**
 * Voting functionality
 */
function initVoting() {
    document.querySelectorAll('.vote-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (!IS_AUTHENTICATED) {
                window.location.href = '/login/';
                return;
            }
            
            const type = this.dataset.type; // 'post' or 'response'
            const id = this.dataset.id;
            const action = this.dataset.action; // 'up' or 'down'
            
            let url;
            if (type === 'post') {
                url = `${FORUM_URLS.votePost}${id}/`;
            } else {
                url = `${FORUM_URLS.voteResponse}${id}/`;
            }
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ vote_type: action })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update vote count
                    const voteCountEl = document.getElementById(`${type}-vote-count-${id}`);
                    if (voteCountEl) {
                        voteCountEl.textContent = data.vote_count;
                    }
                    
                    // Update button states
                    const container = this.closest('.post-actions');
                    const upBtn = container.querySelector('[data-action="up"]');
                    const downBtn = container.querySelector('[data-action="down"]');
                    
                    upBtn.classList.remove('voted');
                    downBtn.classList.remove('voted');
                    
                    if (data.user_vote === 1) {
                        upBtn.classList.add('voted');
                    } else if (data.user_vote === -1) {
                        downBtn.classList.add('voted');
                    }
                }
            })
            .catch(error => {
                console.error('Error voting:', error);
            });
        });
    });
}

/**
 * Main Response Form (at bottom of post)
 */
function initResponseForm() {
    const form = document.getElementById('mainResponseForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const submitBtn = form.querySelector('.btn-submit-reply');
        const textarea = form.querySelector('textarea');
        
        if (!textarea.value.trim()) {
            alert('Please enter a response.');
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Posting...';
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Get post ID from URL or form action
                const postId = form.action.match(/\/forum\/post\/(\d+)\/response\//)?.[1];
                if (postId) {
                    loadPostDetail(postId);
                } else {
                    window.location.reload();
                }
            } else {
                alert('Error posting response: ' + JSON.stringify(data.errors));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error posting response. Please try again.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Post';
        });
    });
}

/**
 * Course Search for New Post Modal
 */
function initCourseSearch() {
    const searchInput = document.getElementById('courseSearch');
    const resultsDiv = document.getElementById('courseResults');
    const courseIdInput = document.getElementById('courseId');
    
    if (!searchInput || !resultsDiv) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            resultsDiv.classList.remove('show');
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetch(`${FORUM_URLS.searchCourses}?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        resultsDiv.innerHTML = data.results.map(course => `
                            <div class="course-result-item" data-id="${course.id}" data-code="${course.code}">
                                <div class="course-result-code">${course.code}</div>
                                <div class="course-result-title">${course.title}</div>
                            </div>
                        `).join('');
                        resultsDiv.classList.add('show');
                        
                        // Add click handlers
                        resultsDiv.querySelectorAll('.course-result-item').forEach(item => {
                            item.addEventListener('click', function() {
                                courseIdInput.value = this.dataset.id;
                                searchInput.value = this.dataset.code;
                                resultsDiv.classList.remove('show');
                            });
                        });
                    } else {
                        resultsDiv.innerHTML = '<div class="course-result-item">No courses found</div>';
                        resultsDiv.classList.add('show');
                    }
                })
                .catch(error => {
                    console.error('Error searching courses:', error);
                });
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
            resultsDiv.classList.remove('show');
        }
    });
    
    // Clear course selection
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Backspace' && courseIdInput.value) {
            courseIdInput.value = '';
        }
    });
}

/**
 * Post Actions (Edit/Delete)
 */
function initPostActions() {
    // Edit post
    document.querySelectorAll('.edit-post-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.dataset.postId;
            // For now, just alert - you could implement an edit modal
            alert('Edit functionality coming soon! Post ID: ' + postId);
        });
    });
    
    // Delete post
    document.querySelectorAll('.delete-post-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.dataset.postId;
            
            if (confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
                fetch(`${FORUM_URLS.deletePost}${postId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': CSRF_TOKEN,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = FORUM_URLS.dashboard;
                    } else {
                        alert('Error deleting post.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error deleting post.');
                });
            }
        });
    });
}

/**
 * Response Actions (Edit/Delete)
 */
function initResponseActions() {
    // Edit response
    document.querySelectorAll('.edit-response-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const responseId = this.dataset.responseId;
            // For now, just alert - you could implement inline editing
            alert('Edit functionality coming soon! Response ID: ' + responseId);
        });
    });
    
    // Delete response
    document.querySelectorAll('.delete-response-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const responseId = this.dataset.responseId;
            
            if (confirm('Are you sure you want to delete this response?')) {
                fetch(`${FORUM_URLS.deleteResponse}${responseId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': CSRF_TOKEN,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reload current post
                        const url = new URL(window.location);
                        const postId = url.searchParams.get('post');
                        if (postId) {
                            loadPostDetail(postId);
                        } else {
                            window.location.reload();
                        }
                    } else {
                        alert('Error deleting response.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error deleting response.');
                });
            }
        });
    });
}