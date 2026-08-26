let selectedAvatarFile = null;
const MAX_AVATAR_SIZE = 10 * 1024 * 1024; // 10 MB


function toggleMenu() {
    const menu = document.getElementById("menuDropdown");
    menu.classList.toggle("show");
}

function openSettings(event) {
    if (event) event.preventDefault();
    const menuDropdown = document.getElementById("menuDropdown");
    menuDropdown?.classList.remove("show");
    const savedUser = JSON.parse(localStorage.getItem("user"));
    logger.debug("Opening settings", {
        userId: savedUser?.id
    });
    if (!savedUser) return;
    openProfile(savedUser, true);
}

function closeSettings(event) {
  if (event) event.preventDefault();
  const overlay = document.getElementById("modalOverlay");
  overlay.classList.remove("active");
}

function toggleEditMode() {
    logger.debug("Profile edit mode toggled", {
        isEditing
    });
    const infoView = document.getElementById("info");
    const infoEdit = document.getElementById("infoEdit");
    const btnEdit = document.querySelector(".btn-edit");
    
    const isEditing = getComputedStyle(infoEdit).display !== "none";
    
    if (isEditing) {
        // Переключаемся в режим просмотра
        infoView.style.display = "flex";
        infoEdit.style.display = "none";
        btnEdit.textContent = "✏️ Редактировать";
        const avatar =
            document.getElementById("avatar");

        avatar.classList.remove("editable-avatar");
        avatar.onclick = null;
    } else {
        // Переключаемся в режим редактирования
        infoView.style.display = "none";
        infoEdit.style.display = "flex";
        btnEdit.style.display = "none";
        const avatar =
            document.getElementById("avatar");

        avatar.classList.add("editable-avatar");

        avatar.onclick = () => {

            document
                .getElementById("avatarInput")
                .click();

        };
        
        // Заполняем форму текущими данными
        const userData = JSON.parse(localStorage.getItem("user"));
        document.getElementById("editUsername").value = userData.username || "";
        document.getElementById("editUsernameid").value = userData.usernameid || "";
        document.getElementById("editBio").value = userData.bio || "";
        document.getElementById("editBirthday").value = userData.birthday || "";
    }
}

async function saveProfile() {

    const username = document.getElementById("editUsername").value.trim();
    const usernameid = document.getElementById("editUsernameid").value.trim();
    const bio = document.getElementById("editBio").value.trim();
    const birthday = document.getElementById("editBirthday").value;
    logger.info("Saving profile", {
        username,
        usernameid,
        hasAvatar: !!selectedAvatarFile
    });
    if (!username) {
        showToast("❌ Имя пользователя не может быть пустым");
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/users/me`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                username: username,
                usernameid: usernameid,
                bio: bio,
                birthday: birthday
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            showToast("❌ Ошибка сохранения: " + (errorData.detail || "Неизвестная ошибка"));
            return;
        }
        
        const updatedUser = await response.json();
        logger.info("Profile saved", {
            userId: updatedUser.id
        });
        if (selectedAvatarFile) {
            const formData = new FormData();
            formData.append(
                "avatar",
                selectedAvatarFile
            );
            logger.debug("Uploading avatar", {
                fileName: selectedAvatarFile.name,
                fileSize: selectedAvatarFile.size,
                fileType: selectedAvatarFile.type
            });
            const avatarResponse = await fetch(
                `${API_URL}/users/me/avatar`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`
                    },
                    body: formData
                }
            );

            if (avatarResponse.ok) {

                logger.info("Avatar uploaded", {
                    userId: updatedUser.id
                });

                const avatarData =
                    await avatarResponse.json();

                updatedUser.avatar =
                    avatarData.avatar;

                renderAvatar(updatedUser);

            } else {

                let errorData = null;

                try {
                    errorData =
                        await avatarResponse.json();
                } catch (e) {
                    // Ответ не содержит JSON
                }

                logger.warn("Avatar upload failed", {
                    userId: updatedUser.id,
                    status: avatarResponse.status,
                    detail: errorData?.detail
                });

                showToast(
                    "❌ Не удалось загрузить аватар"
                );
            }
        }
        
        // Обновляем localStorage БЕЗ выхода
        localStorage.setItem("user", JSON.stringify(updatedUser));
        updateCurrentUser(updatedUser);
        
        // Если был активный чат, переподключаемся к WebSocket
        if (currentChatId && socket) {
            logger.debug("Reconnecting WebSocket after profile update", {
                chatId: currentChatId
            });
            socket.close();
            connectWebSocket();  // 👈 Переподключаемся
        }
        
        // Закрываем редактор и обновляем просмотр
        cancelEditprof();

        renderAvatar(updatedUser);

        // обновляем текст
        document.getElementById("ausername").textContent = updatedUser.username;
        document.getElementById("ausernameid").textContent = updatedUser.usernameid;
        document.getElementById("abio").textContent = updatedUser.bio || "Не указано";
        document.getElementById("ahappy").textContent = updatedUser.birthday || "Не указано";
        
       showToast("✅ Профиль сохранён");
    } catch (error) {
        logger.error("Error saving profile", error);
        showToast("❌ Ошибка при сохранёние");
    }
}

function updateCurrentUser(user) {
    currentUser = user;
    currentUserId = user.id;
    localStorage.setItem("user", JSON.stringify(user));
}


document
    .getElementById("avatarInput")
    .addEventListener(
        "change",
        previewAvatar
    );

function previewAvatar(e) {

    const file =
        e.target.files[0];

    if (!file)
        return;

    if (file.size > MAX_AVATAR_SIZE) {

        logger.warn("Avatar rejected by client validation", {
            fileName: file.name,
            fileSize: file.size,
            limit: MAX_AVATAR_SIZE
        });

        showToast(
            "❌ Аватар слишком большой. Максимальный размер: 10 МБ"
        );

        e.target.value = "";
        selectedAvatarFile = null;

        return;
    }

    if (!file.type.startsWith("image/")) {

        logger.warn("Avatar rejected: invalid MIME type", {
            fileName: file.name,
            fileType: file.type
        });

        showToast(
            "❌ Можно выбрать только изображение"
        );

        e.target.value = "";
        selectedAvatarFile = null;

        return;
    }

    selectedAvatarFile = file;

    const avatar =
        document.getElementById("avatar");

    avatar.innerHTML = "";

    const img =
        document.createElement("img");

    const previewUrl = URL.createObjectURL(file);
    img.src = previewUrl;
    img.onload = () => URL.revokeObjectURL(previewUrl);

    img.className =
        "profile-avatar-image";

    avatar.appendChild(img);

}



function cancelEditprof() {
    selectedAvatarFile = null;

    document.getElementById("avatarInput").value = "";

    const user =
        JSON.parse(localStorage.getItem("user"));

    renderAvatar(user);

    document.getElementById("info").style.display = "flex";
    document.getElementById("infoEdit").style.display = "none";

    const btnEdit =
        document.querySelector(".btn-edit");

    btnEdit.style.display = "block";

    const avatar =
        document.getElementById("avatar");

    avatar.classList.remove("editable-avatar");
    avatar.onclick = null;
}