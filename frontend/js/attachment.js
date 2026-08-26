function initAttachmentModule() {

    const mediaInput = document.getElementById("mediaInput");
    const fileInput = document.getElementById("fileInput");
    const attachBtn = document.getElementById("attachBtn");
    const pickMediaButton = document.getElementById("pickMediaButton");
    const pickFileButton = document.getElementById("pickFileButton");
    const attachmentMenu = document.getElementById("attachmentMenu");

    mediaInput.addEventListener(
        "change",
        e => {

            const file =
                e.target.files[0];

            if (!file) {
                return;
            }
            logger.info("Media file selected", {
                fileName: file.name,
                mimeType: file.type,
                size: file.size
            });
            const validation = validateAttachmentFile(file);

            if (!validation.valid) {
                showToast(`❌ ${validation.message}`);
                e.target.value = "";
                return;
            }
            
            showAttachmentPreview(
                file
            );

            e.target.value = "";

        }
    );
    fileInput.addEventListener(
        "change",
        (e) => {

            const file = e.target.files[0];

            if (!file)
                return;

            logger.info("File selected", {
                fileName: file.name,
                mimeType: file.type,
                size: file.size
            });

            document
                .getElementById("filePreviewIcon")
                .style.background =
                    getFileColor(file.name);
            
            const validation = validateAttachmentFile(file);

            if (!validation.valid) {
                logger.warn("File rejected by client validation", {
                    fileName: file.name,
                    mimeType: file.type,
                    size: file.size,
                    reason: validation.message
                });

                showToast(`❌ ${validation.message}`);
                e.target.value = "";
                return;
            }

            showFilePreview(file);

            e.target.value = "";

        }
    );
    pickMediaButton.addEventListener(
        "click",
        ()=>{

            attachmentMenu.classList.remove(
                "show"
            );

            mediaInput.click();

        }
    );
    pickFileButton.addEventListener(
        "click",
        ()=>{

            attachmentMenu.classList.remove(
                "show"
            );

            fileInput.click();

        }
    );
    attachBtn.addEventListener(
        "click",
        (e)=>{

            e.stopPropagation();

            attachmentMenu.classList.toggle(
                "show"
            );

        }
    );
    document
        .getElementById(
            "cancelAttachmentBtn"
        )
        .addEventListener(
            "click",
            closeAttachmentPreview
        );

    document
        .getElementById("closeFilePreview")
        .addEventListener(
            "click",
            closeFilePreview
        );

    document
        .getElementById("sendFileButton")
        .addEventListener(
            "click",
            async () => {

                if (!selectedAttachment) {
                    return;
                }

                const caption =
                    document
                        .getElementById("fileCaption")
                        .value;

                await sendFile(
                    selectedAttachment,
                    caption
                );

                selectedAttachment = null;

                document
                    .getElementById("fileCaption")
                    .value = "";

                closeFilePreview();
            }
        );

    document
        .getElementById("sendAttachmentBtn")
        .addEventListener(
            "click",
            async () => {

                if (!selectedAttachment) {
                    return;
                }

                const caption =
                    document.getElementById(
                        "attachmentCaption"
                    ).value;

                await sendFile(
                    selectedAttachment,
                    caption
                );

                selectedAttachment = null;

                document.getElementById(
                    "attachmentCaption"
                ).value = "";

                closeAttachmentPreview();
            }
        );
    document.addEventListener("click", ()=> {
        attachmentMenu.classList.remove("show");
    });
    attachmentMenu.addEventListener("click", e=>{
            e.stopPropagation();
    });
}


const FILE_LIMITS = {
    image: 50 * 1024 * 1024,              // 50 MB
    video: 2 * 1024 * 1024 * 1024,        // 2 GB
    document: 250 * 1024 * 1024            // 250 MB
};

function validateAttachmentFile(file) {

    if (!file) {
        return {
            valid: false,
            message: "Файл не выбран"
        };
    }

    const mimeType = file.type || "";

    let limit = FILE_LIMITS.document;
    let typeName = "Документ";

    if (mimeType.startsWith("image/")) {
        limit = FILE_LIMITS.image;
        typeName = "Фото";
    }
    else if (mimeType.startsWith("video/")) {
        limit = FILE_LIMITS.video;
        typeName = "Видео";
    }

    if (file.size > limit) {
        return {
            valid: false,
            message:
                `${typeName} слишком большое. ` +
                `Максимальный размер: ${formatFileSize(limit)}`
        };
    }

    return {
        valid: true
    };
}



function formatFileSize(bytes){

    if(bytes < 1024)
        return bytes + " Б";

    if(bytes < 1024 * 1024)
        return (bytes / 1024).toFixed(1) + " КБ";

    if(bytes < 1024 * 1024 * 1024)
        return (bytes / 1024 / 1024).toFixed(1) + " МБ";

    return (bytes / 1024 / 1024 / 1024).toFixed(1) + " ГБ";

}

function getFileIcon(fileName){

    const ext = fileName
        .split(".")
        .pop()
        .toLowerCase();

    switch(ext){

        case "pdf":
            return "pdf";

        case "doc":
            return "doc";
        case "docx":
            return "doxc";

        case "xls":
            return "xls";

        case "xlsx":
            return "xlsx";

        case "ppt":
            return "ppt";

        case "pptx":
            return "pptx";

        case "zip":
            return "zip";

        case "rar":
            return "rar";

        case "7z":
            return "7z";

        case "txt":
            return "txt";

        case "py":
        case "js":
        case "cpp":
        case "java":
        case "cs":
        case "html":
        case "css":
        case "json":
            return "💻";

        case "mp3":
        case "wav":
        case "ogg":
        case "aac":
            return "🎵";

        default:
            return "📁";
    }

}

function getFileColor(fileName){

    const ext = fileName
        .split(".")
        .pop()
        .toLowerCase();

    switch(ext){

        case "pdf":
            return "#d93025";

        case "doc":
        case "docx":
            return "#2563eb";

        case "xls":
        case "xlsx":
            return "#16a34a";

        case "ppt":
        case "pptx":
            return "#ea580c";

        case "zip":
        case "rar":
        case "7z":
            return "#f59e0b";

        case "txt":
            return "#6b7280";

        default:
            return "#2481cc";
    }

}

async function downloadFile(fileId, fileName) {
    logger.info("File download started", {
        fileId,
        fileName
    });
    const response = await fetch(
        `${API_URL}/files/download/${fileId}`,
        {
            headers: {
                Authorization: `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        logger.error("File download failed", {
            fileId,
            fileName,
            status: response.status
        });
        return;
    }

    const blob = await response.blob();
    logger.info("File downloaded", {
        fileId,
        fileName,
        size: blob.size
    });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;
    a.download = fileName;

    document.body.appendChild(a);

    a.click();

    a.remove();

    URL.revokeObjectURL(url);
}

function showFilePreview(file){

    selectedAttachment = file;

    document
        .getElementById(
            "filePreviewName"
        )
        .textContent =
            file.name;

    document
        .getElementById(
            "filePreviewSize"
        )
        .textContent =
            formatFileSize(
                file.size
            );

    document
        .getElementById(
            "filePreviewIcon"
        )
        .textContent =
            getFileIcon(
                file.name
            );

    const preview =
        document.getElementById(
            "filePreview"
        );

    preview.style.display = "flex";

    requestAnimationFrame(() => {

        preview.classList.add(
            "show"
        );

    });

}

function closeFilePreview() {

    const preview =
        document.getElementById(
            "filePreview"
        );

    preview.classList.remove(
        "show"
    );

    setTimeout(() => {

        preview.style.display = "none";

    }, 200);

    selectedAttachment = null;

    document.getElementById(
        "fileCaption"
    ).value = "";

    document.getElementById("fileInput").value = "";

}

function showAttachmentPreview(file) {

    selectedAttachment = file;

    const image =
        document.getElementById(
            "attachmentPreviewImage"
        );

    const video =
        document.getElementById(
            "attachmentPreviewVideo"
        );

    const url =
        URL.createObjectURL(file);

    image.style.display = "none";
    video.style.display = "none";

    image.src = "";
    video.src = "";

    if (
        file.type.startsWith("image/")
    ) {

        image.src = url;

        image.style.display =
            "block";

    }
    else if (
        file.type.startsWith("video/")
    ) {

        video.src = url;

        video.style.display =
            "block";

    }

    const preview =
        document.getElementById(
            "attachmentPreview"
        );

    preview.style.display = "flex";

    requestAnimationFrame(() => {

        preview.classList.add(
            "show"
        );

    });
}

function closeAttachmentPreview() {

    selectedAttachment = null;

    const preview =
        document.getElementById(
            "attachmentPreview"
        );

    preview.classList.remove(
        "show"
    );

    setTimeout(() => {

        preview.style.display = "none";

    }, 200);

    const image =
        document.getElementById(
            "attachmentPreviewImage"
        );

    const video =
        document.getElementById(
            "attachmentPreviewVideo"
        );

    image.src = "";

    video.pause();
    video.src = "";

    image.style.display = "none";
    video.style.display = "none";

    document.getElementById(
        "attachmentCaption"
    ).value = "";

    mediaInput.value = "";

}

async function sendFile(file, caption = "") {
    const validation = validateAttachmentFile(file);

    if (!validation.valid) {
        logger.warn("File upload rejected by client validation", {
            fileName: file?.name,
            mimeType: file?.type,
            size: file?.size,
            reason: validation.message
        });

        showToast(`❌ ${validation.message}`);
        return;
    }

    logger.info("File upload started", {
        fileName: file.name,
        mimeType: file.type,
        size: file.size
    });
    try {

        const formData = new FormData();

        formData.append(
            "file",
            file
        );

        const uploadResponse = await fetch(
            `${API_URL}/files/upload`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                },
                body: formData
            }
        );

        if (!uploadResponse.ok) {
            let message = "Не удалось загрузить файл";

            if (uploadResponse.status === 413) {
                message = "Файл слишком большой";
            }

            logger.error("File upload failed", {
                fileName: file.name,
                status: uploadResponse.status
            });

            showToast(`❌ ${message}`);
            return;
        }
        const uploadedFile = await uploadResponse.json();
        logger.info("File uploaded", {
            fileName: file.name,
            fileId: uploadedFile.id
        });
        sendSocket({
            type: "message",
            content: caption,
            file_id: uploadedFile.id
        });
        logger.info("File message sent", {
            fileId: uploadedFile.id,
            fileName: file.name
        });
    } catch (error) {
        logger.error("File upload error", error);
    }
}

