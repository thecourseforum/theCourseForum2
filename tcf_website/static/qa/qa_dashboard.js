document.addEventListener('DOMContentLoaded', function() {
    // Modal elements
    const modal = document.getElementById('newPostModal');
    const newPostBtn = document.querySelector('.btn-new-post');
    const closeModalBtn = document.getElementById('closeModal');
    const cancelModalBtn = document.getElementById('cancelModal');
    const newPostForm = document.getElementById('newPostForm');
    const tagsSelect = document.getElementById('postTags');

    // Open modal
    newPostBtn.addEventListener('click', function() {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    });

    // Close modal functions
    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        newPostForm.reset();
    }

    closeModalBtn.addEventListener('click', closeModal);
    cancelModalBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Handle form submission
    newPostForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = {
            title: document.getElementById('postTitle').value,
            description: document.getElementById('postDescription').value,
            primaryTag: document.getElementById('primaryTag').value,
            tags: Array.from(tagsSelect.selectedOptions).map(opt => opt.value)
        };

        console.log('New post data:', formData);

        // TODO: Send data to backend
        // For now, just close the modal
        closeModal();

        // Show success message (placeholder)
        alert('Post created successfully!');
    });
});
