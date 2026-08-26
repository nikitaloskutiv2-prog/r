const mediaViewer = document.getElementById("mediaViewer");
const mediaViewerImage = document.getElementById("mediaViewerImage");
const mediaViewerVideo = document.getElementById("mediaViewerVideo");

function initUI() {

    document
        .getElementById("mediaViewerClose")
        .addEventListener("click", closeMediaViewer);

    mediaViewer.addEventListener("click", e => {
        if (e.target === mediaViewer) {
            closeMediaViewer();
        }
    });

    document.addEventListener("keydown", e => {
        if (e.key === "Escape") {
            closeMediaViewer();
        }
    });
}

function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") {
        document.body.classList.add("dark-theme");
        document.getElementById("themeToggle").classList.add("active");
    }
}

function toggleTheme() {
    document.body.classList.toggle("dark-theme");
    const themeToggle = document.getElementById("themeToggle");
    themeToggle.classList.toggle("active");
    
    const isDark = document.body.classList.contains("dark-theme");
    localStorage.setItem("theme", isDark ? "dark" : "light");
}

function showChat() {
    if (!isMobile) return;
    
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("mainContent");
    
    sidebar.classList.add("hidden");
    mainContent.classList.remove("hidden");
    mainContent.classList.add("show");
}

function goBack() {
    if (!isMobile) return;
    
    const sidebar = document.getElementById("sidebar");
    const mainContent = document.getElementById("mainContent");
    
    sidebar.classList.remove("hidden");
    mainContent.classList.add("hidden");
    mainContent.classList.remove("show");
    
    // Закрываем меню при возврате
    document.getElementById("menuDropdown").classList.remove("show");
    document.getElementById("chatMoreMenu")?.classList.remove("show");
}

function showToast(text) {
    const toast = document.getElementById("toast");
    toast.textContent = text;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

function openMediaViewer(
    file
) {

    mediaViewer.classList.add(
        "active"
    );

    mediaViewerImage.style.display =
        "none";

    mediaViewerVideo.style.display =
        "none";

    if (
        file.mime_type.startsWith(
            "image/"
        )
    ) {

        mediaViewerImage.src =
            `${API_URL}/${file.path}`;

        mediaViewerImage.style.display =
            "block";

    } else {

        mediaViewerVideo.src =
            `${API_URL}/${file.path}`;

        mediaViewerVideo.style.display =
            "block";

        mediaViewerVideo.play();
    }
}

function closeMediaViewer() {

    mediaViewer.classList.remove(
        "active"
    );

    mediaViewerVideo.pause();

    mediaViewerVideo.src = "";

    mediaViewerImage.src = "";
}


function updateMessageReadStatus(messageId) {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
        const badges = messageElement.querySelector(".message-status-badges");
        if (badges) {
            badges.classList.remove("unread");
            badges.textContent = "✓✓";
        }
    }
}




