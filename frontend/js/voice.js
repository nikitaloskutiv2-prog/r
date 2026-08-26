let mediaRecorder = null;
let audioChunks = [];

let recordingTimer = null;
let recordingSeconds = 0;
const MAX_VOICE_DURATION = 2 * 60 * 60; // 2 часа

let recordedBlob = null;

let audioContext = null;
let analyser = null;
let sourceNode = null;

let waveformData = [];
let waveformInterval = null;

function getRecordingIndicator() {
    return document.getElementById("recordingIndicator");
}

function formatRecordingTime(seconds) {

    const h = String(Math.floor(seconds / 3600)).padStart(2, "0");
    const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");

    return `${h}:${m}:${s}`;

}

function formatVoiceDuration(seconds) {

    const h = Math.floor(seconds / 3600);

    const m = Math.floor((seconds % 3600) / 60);

    const s = seconds % 60;

    if (h > 0) {

        return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;

    }

    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;

}

function startRecordingTimer() {

    recordingSeconds = 0;

    const indicator = getRecordingIndicator();

    if (!indicator)
        return;

    indicator.style.display = "flex";

    indicator.innerHTML =
        `<span class="rec-dot"></span> 00:00:00`;

    recordingTimer = setInterval(() => {

        recordingSeconds++;

        indicator.innerHTML =
            `<span class="rec-dot"></span> ${formatRecordingTime(recordingSeconds)}`;

        if (recordingSeconds >= MAX_VOICE_DURATION) {

            logger.info(
                "Voice recording paused at maximum duration",
                {
                    duration: recordingSeconds,
                    limit: MAX_VOICE_DURATION
                }
            );

            clearInterval(recordingTimer);
            recordingTimer = null;

            pauseVoiceRecordingAtLimit();

        }

    }, 1000);

}

function pauseVoiceRecordingAtLimit() {

    if (!mediaRecorder || !isRecording)
        return;

    mediaRecorder.onstop = () => {

        recordedBlob = new Blob(
            audioChunks,
            {
                type: "audio/webm"
            }
        );

        mediaRecorder.stream
            .getTracks()
            .forEach(track => track.stop());

        mediaRecorder = null;

        isRecording = false;

        logger.info(
            "Voice recording paused at maximum duration",
            {
                duration: recordingSeconds
            }
        );

    };
    clearInterval(waveformInterval);
    waveformInterval = null;

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    mediaRecorder.stop();

    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {

        sendSocket({
            type: "voice_recording_stop"
        });

    }

    messageInput.disabled = false;
    messageInput.placeholder = "Голосовое сообщение готово к отправке";

    stopRecordingTimer();

}

function stopRecordingTimer() {

    clearInterval(recordingTimer);
    recordingTimer = null;

    const indicator = getRecordingIndicator();

    if (!indicator)
        return;

    indicator.style.display = "none";
    indicator.innerHTML = "";

}

function resetVoiceUI() {

    isRecording = false;

    voiceBtn.style.display = "flex";
    sendBtn.style.display = "none";
    cancelVoiceBtn.style.display = "none";

    messageInput.disabled = false;
    messageInput.placeholder = "Напишите сообщение...";

    stopRecordingTimer();

}

async function startVoiceRecording() {

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });
        
        audioContext =
    new AudioContext();

    sourceNode =
        audioContext.createMediaStreamSource(stream);

    analyser =
        audioContext.createAnalyser();

    analyser.fftSize = 256;

    sourceNode.connect(analyser);

    waveformData = [];

    const dataArray =
        new Float32Array(analyser.fftSize);

    waveformInterval =
        setInterval(() => {

            analyser.getFloatTimeDomainData(dataArray);

            let sum = 0;

            for (let i = 0; i < dataArray.length; i++) {

                sum += dataArray[i] * dataArray[i];

            }

            const rms =
                Math.sqrt(sum / dataArray.length);

            waveformData.push(rms);

        }, 20);

        audioChunks = [];
        recordedBlob = null;

        const options = {
            mimeType: "audio/webm;codecs=opus",
            audioBitsPerSecond: 20000
        };

        if (
            MediaRecorder.isTypeSupported(
                options.mimeType
            )
        ) {

            mediaRecorder =
                new MediaRecorder(
                    stream,
                    options
                );

        } else {

            mediaRecorder =
                new MediaRecorder(stream);

        }

        mediaRecorder.ondataavailable = (e) => {

            if (e.data.size > 0)
                audioChunks.push(e.data);

        };

        mediaRecorder.start();
        if (
            socket &&
            socket.readyState === WebSocket.OPEN
        ) {
            sendSocket({
                type: "voice_recording"
            });
        }
        isRecording = true;

        messageInput.disabled = true;
        const isMobile = window.innerWidth <= 425;
        messageInput.placeholder = isMobile ? '' : 'Идёт запись...';

        voiceBtn.style.display = "none";
        sendBtn.style.display = "flex";
        cancelVoiceBtn.style.display = "flex";

        startRecordingTimer();

    } catch (err) {

        logger.error(
            "Ошибка запуска записи голосового сообщения",
            err
        );

        showToast("Нет доступа к микрофону");

    }

}




async function sendVoiceMessage() {

    if (!recordedBlob)
        return;

    const duration = await getAudioDuration(recordedBlob);
    const safeDuration = Math.min(
        duration,
        MAX_VOICE_DURATION
    );
    clearInterval(waveformInterval);
    waveformInterval = null;

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    waveformData =
        compressWaveform(waveformData);
    
    waveformData =
        smoothWaveform(
                waveformData
            
        );


    const max = Math.max(...waveformData, 0);

    if (max > 0) {

        waveformData =
            waveformData.map(v =>
                Math.round((v / max) * 100)
            );

    } else {

        waveformData =
            waveformData.map(() => 0);

    }

    const formData = new FormData();

    formData.append(
        "voice",
        recordedBlob,
        "voice.webm"
    );

    formData.append(
        "chat_id",
        currentChatId
    );

    formData.append(
        "waveform",
        JSON.stringify(waveformData)
    );
    formData.append(
        "duration",
        safeDuration
    );
    let data;

    try {

        const response = await fetch(
            `${API_URL}/messages/voice`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                },
                body: formData
            }
        );

        if (!response.ok) {

            showToast("Ошибка отправки");
            return;

        }

        data = await response.json();

    } catch (err) {

        logger.error(
            "Ошибка отправки голосового сообщения",
            err
        );

        showToast("Ошибка отправки");
        return;

    }

    if (!data.file_id) {

        showToast("Ошибка сервера");
        return;

    }

    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {

        socket.send(JSON.stringify({
            type: "message",
            content: null,
            file_id: data.file_id,
            voice_duration: safeDuration,
            waveform: waveformData
        }));
        sendSocket({
            type: "voice_recording_stop"
        });

    } else {

        showToast("Нет соединения с сервером");
        return;

    }

    recordedBlob = null;
    audioChunks = [];
    mediaRecorder = null;


    resetVoiceUI();
    updateInputButtons();

}

function stopVoiceRecording() {

    if (!mediaRecorder) {

        if (recordedBlob) {

            recordedBlob = null;
            audioChunks = [];
            isRecording = false;

            resetVoiceUI();
            updateInputButtons();

        }

        return;
    }
    mediaRecorder.onstop = () => {

        mediaRecorder.stream
            .getTracks()
            .forEach(track => track.stop());

        audioChunks = [];
        recordedBlob = null;
        mediaRecorder = null;

    };

    mediaRecorder.stop();
    clearInterval(waveformInterval);
    waveformInterval = null;

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    if (
        socket &&
        socket.readyState === WebSocket.OPEN
    ) {
        sendSocket({
            type: "voice_recording_stop"
        });
    }

    resetVoiceUI();

}


function getAudioDuration(blob) {

    return new Promise((resolve) => {

        const audio = document.createElement("audio");

        audio.preload = "metadata";

        audio.onloadedmetadata = () => {

            URL.revokeObjectURL(audio.src);

            resolve(Math.round(audio.duration));

        };

        audio.src = URL.createObjectURL(blob);

    });

}

function compressWaveform(data, target = 40) {

    if (data.length <= target)
        return data;

    const result = [];

    const step = data.length / target;

    for (let i = 0; i < target; i++) {

        const start = Math.floor(i * step);
        const end = Math.floor((i + 1) * step);

        let sum = 0;
        let count = 0;

        for (let j = start; j < end; j++) {

            sum += data[j];
            count++;

        }

        result.push(count ? sum / count : 0);

    }

    return result;

}

function drawWaveformFromData(
    data,
    canvas
) {

    if (!data?.length)
        return;

    const ctx =
        canvas.getContext("2d");

    const width = 120;
    const height = 25;

    canvas.width = width;
    canvas.height = height;

    ctx.clearRect(
        0,
        0,
        width,
        height
    );

    const progress =
        Number(canvas.dataset.progress || 0);

    const playedBars =
        Math.floor(progress * data.length);

    const barWidth =
        width / data.length;

    for (let i = 0; i < data.length; i++) {

        const value =
            Math.pow(
                data[i] / 100,
                0.35
            );

        const barHeight =
            Math.max(5,value * height * 0.75);

        ctx.fillStyle =
            i <= playedBars
                ? "#4ea1ff"
                : "#8aa8d6";

        ctx.beginPath();
        ctx.fillRect(
            i * barWidth,
            (height - barHeight) / 2,
            barWidth * 0.55,
            barHeight
        );
        ctx.fill();

    }

}

function smoothWaveform(data) {

    const result = [];

    for (let i = 0; i < data.length; i++) {

        const prev =
            data[i - 1] ?? data[i];

        const cur =
            data[i];

        const next =
            data[i + 1] ?? data[i];

        result.push(
            (prev + cur + next) / 3
        );

    }

    return result;

}




sendBtn.onclick = () => {

    if (!isRecording && recordedBlob) {

        sendVoiceMessage();
        return;

    }

    if (!isRecording) {

        handleSend();
        return;

    }

    mediaRecorder.onstop = async () => {

        recordedBlob = new Blob(
            audioChunks,
            {
                type: "audio/webm"
            }
        );

        mediaRecorder.stream
            .getTracks()
            .forEach(track => track.stop());

        await sendVoiceMessage();

    };

    mediaRecorder.stop();

};

cancelVoiceBtn.onclick = () => {

    stopVoiceRecording();

};


