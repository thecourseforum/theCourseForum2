function openModal() {
    document.getElementById("newPostModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("newPostModal").style.display = "none";
}

document.querySelector(".btn-new-post")
    .addEventListener("click", openModal);