document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("videoPlayer");
    const overlay = document.getElementById("autoplayOverlay");
    const watchShell = document.querySelector(".watch-shell");
    const nextUrl = watchShell?.dataset.nextUrl || "";

    const autoplayToggle = document.getElementById("autoplayToggle");
    const autoplayDelaySelect = document.getElementById("autoplayDelaySelect");
    const openSettings = document.getElementById("openSettings");
    const closeSettings = document.getElementById("closeSettings");
    const settingsPanel = document.getElementById("settingsPanel");
    const cancelBtn = document.getElementById("cancelAutoplay");

    let autoplayEnabled = true;
    let autoplayDelay = 10;
    let countdown = autoplayDelay;
    let interval = null;

    const loadSettings = () => {
        try {
            const raw = localStorage.getItem("metflixSettings");
            if (!raw) {
                return;
            }
            const parsed = JSON.parse(raw);
            if (typeof parsed.autoplayEnabled === "boolean") {
                autoplayEnabled = parsed.autoplayEnabled;
            }
            if (typeof parsed.autoplayDelay === "number") {
                autoplayDelay = parsed.autoplayDelay;
            }
        } catch (error) {}
    };

    const saveSettings = () => {
        localStorage.setItem(
            "metflixSettings",
            JSON.stringify({ autoplayEnabled, autoplayDelay })
        );
    };

    const showSettings = () => {
        if (settingsPanel) {
            settingsPanel.classList.remove("hidden");
        }
    };

    const hideSettings = () => {
        if (settingsPanel) {
            settingsPanel.classList.add("hidden");
        }
    };

    const startAutoplayCountdown = () => {
        if (!overlay || !nextUrl || !autoplayEnabled) {
            return;
        }

        overlay.classList.remove("hidden");
        const countdownSpan = document.getElementById("countdown");
        countdown = autoplayDelay;
        if (countdownSpan) {
            countdownSpan.textContent = countdown;
        }

        interval = setInterval(() => {
            countdown -= 1;
            if (countdownSpan) {
                countdownSpan.textContent = countdown;
            }

            if (countdown <= 0) {
                clearInterval(interval);
                window.location.href = nextUrl;
            }
        }, 1000);
    };

    loadSettings();

    if (autoplayToggle) {
        autoplayToggle.checked = autoplayEnabled;
        autoplayToggle.addEventListener("change", () => {
            autoplayEnabled = autoplayToggle.checked;
            saveSettings();
        });
    }

    if (autoplayDelaySelect) {
        autoplayDelaySelect.value = String(autoplayDelay);
        autoplayDelaySelect.addEventListener("change", () => {
            autoplayDelay = Number(autoplayDelaySelect.value) || 10;
            saveSettings();
        });
    }

    if (openSettings) {
        openSettings.addEventListener("click", showSettings);
    }
    if (closeSettings) {
        closeSettings.addEventListener("click", hideSettings);
    }
    if (settingsPanel) {
        settingsPanel.addEventListener("click", (event) => {
            if (event.target === settingsPanel) {
                hideSettings();
            }
        });
    }

    if (video) {
        video.addEventListener("ended", () => {
            if (nextUrl) {
                startAutoplayCountdown();
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            clearInterval(interval);
            if (overlay) {
                overlay.classList.add("hidden");
            }
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key.toLowerCase() === "f" && video) {
            if (!document.fullscreenElement) {
                video.requestFullscreen().catch(() => {});
            } else {
                document.exitFullscreen().catch(() => {});
            }
        }
    });
});
