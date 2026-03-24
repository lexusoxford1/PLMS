document.addEventListener("DOMContentLoaded", () => {
    const toastStack = document.querySelector("[data-toast-stack]");
    createNotifier(toastStack);

    initializeAppShell();
    initializeExistingToasts();
    initializeBadgeCelebration();
    initializeBadgeDetailModals();
    initializeMilestoneCarousel();
    initializeLessonSlideViewer();
    initializeProfilePanels();
    initializeCodeRunnerForms();
    initializeRunnerResetButtons();
});

function initializeAppShell() {
    const shell = document.querySelector("[data-app-shell]");
    if (!shell) {
        return;
    }

    const body = document.body;
    const sidebar = shell.querySelector("[data-app-sidebar]");
    const sidebarToggleButtons = Array.from(shell.querySelectorAll("[data-app-sidebar-toggle]"));
    const sidebarCloseButtons = Array.from(shell.querySelectorAll("[data-app-sidebar-close]"));
    const navModeButtons = Array.from(shell.querySelectorAll("[data-app-nav-mode-toggle]"));
    const userMenu = shell.querySelector("[data-user-menu]");
    const mobileBreakpoint = window.matchMedia("(max-width: 1080px)");
    const compactStorageKey = "plms-app-sidebar-compact";
    const getSavedCompactState = () => window.localStorage.getItem(compactStorageKey) === "true";

    const applyCompactState = (compact) => {
        const shouldCompact = !mobileBreakpoint.matches && compact;
        body.classList.toggle("app-shell-nav-compact", shouldCompact);

        navModeButtons.forEach((button) => {
            button.setAttribute("aria-pressed", shouldCompact ? "true" : "false");
            button.setAttribute(
                "aria-label",
                shouldCompact ? "Switch to navigation with labels" : "Switch to icon-only navigation"
            );
            button.setAttribute(
                "title",
                shouldCompact ? "Expanded navigation" : "Compact navigation"
            );
        });
    };

    const applySidebarState = (open) => {
        const shouldOpen = mobileBreakpoint.matches && open;
        body.classList.toggle("app-shell-sidebar-open", shouldOpen);

        if (sidebar) {
            sidebar.setAttribute("aria-hidden", shouldOpen ? "false" : mobileBreakpoint.matches ? "true" : "false");
        }

        sidebarToggleButtons.forEach((button) => {
            button.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
        });
    };

    sidebarToggleButtons.forEach((button) => {
        button.addEventListener("click", () => {
            applySidebarState(!body.classList.contains("app-shell-sidebar-open"));
        });
    });

    sidebarCloseButtons.forEach((button) => {
        button.addEventListener("click", () => applySidebarState(false));
    });

    navModeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const nextCompactState = !body.classList.contains("app-shell-nav-compact");
            applyCompactState(nextCompactState);
            window.localStorage.setItem(compactStorageKey, nextCompactState ? "true" : "false");
        });
    });

    if (userMenu) {
        userMenu.querySelectorAll("a, button").forEach((item) => {
            item.addEventListener("click", () => {
                userMenu.open = false;
            });
        });

        document.addEventListener("click", (event) => {
            if (userMenu.open && !userMenu.contains(event.target)) {
                userMenu.open = false;
            }
        });
    }

    const handleViewportChange = () => {
        applySidebarState(false);
        applyCompactState(getSavedCompactState());
    };

    if (typeof mobileBreakpoint.addEventListener === "function") {
        mobileBreakpoint.addEventListener("change", handleViewportChange);
    } else if (typeof mobileBreakpoint.addListener === "function") {
        mobileBreakpoint.addListener(handleViewportChange);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }

        applySidebarState(false);
        if (userMenu && userMenu.open) {
            userMenu.open = false;
        }
    });

    applySidebarState(false);
    applyCompactState(getSavedCompactState());
}

function initializeProfilePanels() {
    document.querySelectorAll("[data-profile-workspace]").forEach((workspace) => {
        const triggers = Array.from(workspace.querySelectorAll("[data-profile-nav]"));
        const navButtons = Array.from(workspace.querySelectorAll(".profile-sidebar__nav-button[data-profile-nav]"));
        const panels = Array.from(workspace.querySelectorAll("[data-profile-panel]"));
        const toggleButton = workspace.querySelector("[data-profile-toggle]");
        if (!triggers.length || !panels.length) {
            return;
        }

        const validPanels = new Set(panels.map((panel) => panel.dataset.profilePanel));
        const collapseStorageKey = "plms-profile-sidebar-collapsed";
        const defaultPanel = validPanels.has(workspace.dataset.defaultPanel)
            ? workspace.dataset.defaultPanel
            : panels[0].dataset.profilePanel;
        const savedCollapsedState = window.localStorage.getItem(collapseStorageKey);

        const resolveHashPanel = () => {
            const hash = window.location.hash || "";
            if (!hash.startsWith("#profile-")) {
                return "";
            }
            const panelId = hash.replace("#profile-", "");
            return validPanels.has(panelId) ? panelId : "";
        };

        const applyCollapsedState = (collapsed) => {
            workspace.classList.toggle("is-collapsed", collapsed);
            if (!toggleButton) {
                return;
            }

            toggleButton.setAttribute("aria-expanded", collapsed ? "false" : "true");
            toggleButton.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
            toggleButton.setAttribute("title", collapsed ? "Expand sidebar" : "Collapse sidebar");
        };

        const activatePanel = (panelId, updateHash = true) => {
            if (!validPanels.has(panelId)) {
                return;
            }

            panels.forEach((panel) => {
                panel.hidden = panel.dataset.profilePanel !== panelId;
            });

            navButtons.forEach((button) => {
                const isActive = button.dataset.profileNav === panelId;
                button.classList.toggle("is-active", isActive);
                button.setAttribute("aria-selected", isActive ? "true" : "false");
            });

            if (updateHash) {
                const nextHash = `#profile-${panelId}`;
                if (window.location.hash !== nextHash) {
                    history.replaceState(null, "", nextHash);
                }
            }
        };

        triggers.forEach((trigger) => {
            trigger.addEventListener("click", () => {
                activatePanel(trigger.dataset.profileNav);
            });
        });

        if (toggleButton) {
            toggleButton.addEventListener("click", () => {
                const collapsed = !workspace.classList.contains("is-collapsed");
                applyCollapsedState(collapsed);
                window.localStorage.setItem(collapseStorageKey, collapsed ? "true" : "false");
            });
        }

        window.addEventListener("hashchange", () => {
            const hashPanel = resolveHashPanel();
            if (hashPanel) {
                activatePanel(hashPanel, false);
            }
        });

        applyCollapsedState(
            savedCollapsedState === null ? window.innerWidth < 1180 : savedCollapsedState === "true"
        );
        activatePanel(resolveHashPanel() || defaultPanel, false);
    });
}

function createNotifier(toastStack) {
    const notify = ({ level = "info", title = "Notice", message = "", duration = 4800 }) => {
        if (!toastStack) {
            return;
        }

        const toast = document.createElement("div");
        toast.className = `toast ${level}`;
        toast.setAttribute("data-toast", "");

        const content = document.createElement("div");
        content.className = "toast-content";

        const heading = document.createElement("strong");
        heading.className = "toast-title";
        heading.textContent = title;

        const body = document.createElement("p");
        body.textContent = message;

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = "toast-close";
        closeButton.setAttribute("data-toast-close", "");
        closeButton.setAttribute("aria-label", "Dismiss notification");
        closeButton.innerHTML = "&times;";

        content.appendChild(heading);
        content.appendChild(body);
        toast.appendChild(content);
        toast.appendChild(closeButton);
        toastStack.appendChild(toast);

        activateToast(toast, duration);
    };

    window.PLMS = Object.assign(window.PLMS || {}, { notify });
    return notify;
}

function initializeExistingToasts() {
    document.querySelectorAll("[data-toast]").forEach((toast, index) => {
        activateToast(toast, 4800 + index * 250);
    });
}

function activateToast(toast, duration) {
    if (toast.dataset.ready === "true") {
        return;
    }

    toast.dataset.ready = "true";
    const closeButton = toast.querySelector("[data-toast-close]");
    if (closeButton) {
        closeButton.addEventListener("click", () => dismissToast(toast));
    }

    requestAnimationFrame(() => {
        toast.classList.add("visible");
    });

    window.setTimeout(() => dismissToast(toast), duration);
}

function dismissToast(toast) {
    if (!toast || toast.dataset.closing === "true") {
        return;
    }

    toast.dataset.closing = "true";
    toast.classList.remove("visible");
    toast.classList.add("closing");
    window.setTimeout(() => toast.remove(), 220);
}

function initializeBadgeCelebration() {
    const celebration = document.querySelector("[data-badge-celebration]");
    if (!celebration) {
        return;
    }

    const slides = Array.from(celebration.querySelectorAll("[data-badge-slide]"));
    const progress = celebration.querySelector("[data-badge-progress]");
    const nextButton = celebration.querySelector("[data-badge-next]");
    const closeButtons = celebration.querySelectorAll("[data-badge-close]");
    const dialog = celebration.querySelector(".badge-celebration__dialog");
    let activeIndex = 0;

    if (!slides.length) {
        return;
    }

    const updateSlide = () => {
        slides.forEach((slide, index) => {
            slide.hidden = index !== activeIndex;
        });

        if (progress) {
            progress.textContent = `${activeIndex + 1} / ${slides.length}`;
        }

        if (nextButton) {
            nextButton.textContent = activeIndex === slides.length - 1 ? "Continue" : "Next Badge";
        }
    };

    const closeCelebration = () => {
        celebration.classList.remove("visible");
        window.setTimeout(() => {
            celebration.hidden = true;
            celebration.remove();
        }, 220);
    };

    closeButtons.forEach((button) => {
        button.addEventListener("click", closeCelebration);
    });

    if (nextButton) {
        nextButton.addEventListener("click", () => {
            if (activeIndex < slides.length - 1) {
                activeIndex += 1;
                updateSlide();
                return;
            }
            closeCelebration();
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && document.body.contains(celebration)) {
            closeCelebration();
        }
    });

    updateSlide();
    celebration.hidden = false;
    requestAnimationFrame(() => {
        celebration.classList.add("visible");
        if (dialog) {
            if (!dialog.hasAttribute("tabindex")) {
                dialog.setAttribute("tabindex", "-1");
            }
            dialog.focus({ preventScroll: true });
        }
    });

    if (window.PLMS && typeof window.PLMS.notify === "function") {
        window.PLMS.notify({
            level: "success",
            title: "Badge unlocked",
            message: "Your new achievement has been added to the collection.",
            duration: 3600,
        });
    }
}

function initializeBadgeDetailModals() {
    const modal = document.querySelector("[data-badge-detail-modal]");
    if (!modal) {
        return;
    }

    const dialog = modal.querySelector(".badge-detail-modal__dialog");
    const content = modal.querySelector("[data-badge-detail-content]");
    const closeButtons = Array.from(modal.querySelectorAll("[data-badge-detail-close]"));
    const triggers = Array.from(document.querySelectorAll("[data-badge-detail-trigger]"));
    let activeTrigger = null;
    let closeTimer = 0;

    if (!dialog || !content || !triggers.length) {
        return;
    }

    const clearExpandedState = () => {
        triggers.forEach((trigger) => {
            trigger.setAttribute("aria-expanded", "false");
        });
    };

    const closeModal = () => {
        if (modal.hidden) {
            return;
        }

        modal.classList.remove("visible");
        document.body.classList.remove("badge-detail-modal-open");
        clearExpandedState();

        const triggerToFocus = activeTrigger;
        activeTrigger = null;

        if (closeTimer) {
            window.clearTimeout(closeTimer);
        }

        closeTimer = window.setTimeout(() => {
            modal.hidden = true;
            content.replaceChildren();

            if (triggerToFocus) {
                triggerToFocus.focus({ preventScroll: true });
            }
        }, 220);
    };

    const openModal = (trigger) => {
        const templateId = trigger.dataset.badgeDetailTemplate;
        const template = templateId ? document.getElementById(templateId) : null;

        if (!(template instanceof HTMLTemplateElement)) {
            return;
        }

        if (closeTimer) {
            window.clearTimeout(closeTimer);
            closeTimer = 0;
        }

        content.replaceChildren(template.content.cloneNode(true));
        clearExpandedState();
        activeTrigger = trigger;
        trigger.setAttribute("aria-expanded", "true");
        modal.hidden = false;
        document.body.classList.add("badge-detail-modal-open");

        window.requestAnimationFrame(() => {
            modal.classList.add("visible");

            const initialFocus = modal.querySelector("[data-badge-detail-initial-focus]") || dialog;
            initialFocus.focus({ preventScroll: true });
        });
    };

    triggers.forEach((trigger) => {
        trigger.addEventListener("click", () => openModal(trigger));
        trigger.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" && event.key !== " ") {
                return;
            }

            event.preventDefault();
            openModal(trigger);
        });
    });

    closeButtons.forEach((button) => {
        button.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !modal.hidden) {
            closeModal();
        }
    });
}

function initializeMilestoneCarousel() {
    document.querySelectorAll("[data-milestone-carousel]").forEach((carousel) => {
        const track = carousel.querySelector("[data-carousel-track]");
        const prevButton = carousel.querySelector("[data-carousel-prev]");
        const nextButton = carousel.querySelector("[data-carousel-next]");
        const currentCounter = carousel.querySelector("[data-carousel-current]");
        const currentLabel = carousel.querySelector("[data-carousel-current-label]");
        const totalCounter = carousel.querySelector("[data-carousel-total]");
        const progressFill = carousel.querySelector("[data-carousel-progress]");
        const dots = Array.from(carousel.querySelectorAll("[data-carousel-dot]"));
        const items = Array.from(carousel.querySelectorAll("[data-carousel-item]"));
        let frameId = 0;
        let resizeFrameId = 0;
        let activeIndex = 0;

        if (!track || !prevButton || !nextButton || !items.length) {
            return;
        }

        if (totalCounter) {
            totalCounter.textContent = `${items.length}`;
        }

        const updateTrackInset = () => {
            const firstItem = items[0];
            if (!firstItem) {
                return;
            }

            const inset = Math.max((track.clientWidth - firstItem.offsetWidth) / 2, 12);
            track.style.setProperty("--milestone-track-inset", `${inset}px`);
        };

        const getSlideLabel = (item) => {
            const title = item.querySelector(".achievement-card__body h3");
            return title ? title.textContent.trim() : "";
        };

        const updateActiveSlides = (nextActiveIndex) => {
            activeIndex = Math.max(0, Math.min(items.length - 1, nextActiveIndex));

            items.forEach((item, index) => {
                const isActive = index === activeIndex;
                item.classList.toggle("is-active", isActive);
                item.classList.toggle("is-nearby", Math.abs(index - activeIndex) === 1);
                item.setAttribute("aria-current", isActive ? "true" : "false");
            });

            dots.forEach((dot, index) => {
                const isActive = index === activeIndex;
                dot.classList.toggle("is-active", isActive);
                dot.setAttribute("aria-pressed", isActive ? "true" : "false");
            });

            if (currentCounter) {
                currentCounter.textContent = `${activeIndex + 1}`;
            }

            if (currentLabel) {
                currentLabel.textContent = getSlideLabel(items[activeIndex]);
            }

            if (progressFill) {
                const completion = items.length === 1 ? 100 : ((activeIndex + 1) / items.length) * 100;
                progressFill.style.width = `${completion}%`;
            }
        };

        const alignActiveSlide = (behavior = "auto") => {
            const target = items[activeIndex];
            if (!target) {
                return;
            }

            const maxScroll = Math.max(track.scrollWidth - track.clientWidth, 0);
            const targetLeft = target.offsetLeft - ((track.clientWidth - target.offsetWidth) / 2);

            track.scrollTo({
                left: Math.max(0, Math.min(targetLeft, maxScroll)),
                behavior,
            });
        };

        const updateCarouselState = () => {
            updateTrackInset();
            const maxScroll = Math.max(track.scrollWidth - track.clientWidth, 0);
            const isScrollable = maxScroll > 6;
            const currentIndex = getActiveIndex();
            const atStart = currentIndex === 0;
            const atEnd = currentIndex === items.length - 1;

            prevButton.disabled = !isScrollable || atStart;
            nextButton.disabled = !isScrollable || atEnd;
            prevButton.setAttribute("aria-disabled", prevButton.disabled ? "true" : "false");
            nextButton.setAttribute("aria-disabled", nextButton.disabled ? "true" : "false");

            carousel.classList.toggle("is-at-start", atStart);
            carousel.classList.toggle("is-at-end", atEnd);
            carousel.classList.toggle("is-static", !isScrollable);
            updateActiveSlides(currentIndex);
        };

        const requestStateUpdate = () => {
            if (frameId) {
                return;
            }

            frameId = window.requestAnimationFrame(() => {
                frameId = 0;
                updateCarouselState();
            });
        };

        const getActiveIndex = () => {
            const trackRect = track.getBoundingClientRect();
            const trackCenter = trackRect.left + (trackRect.width / 2);
            let currentIndex = 0;
            let nearestDistance = Number.POSITIVE_INFINITY;

            items.forEach((item, index) => {
                const itemRect = item.getBoundingClientRect();
                const itemCenter = itemRect.left + (itemRect.width / 2);
                const distance = Math.abs(itemCenter - trackCenter);

                if (distance < nearestDistance) {
                    nearestDistance = distance;
                    currentIndex = index;
                }
            });

            return currentIndex;
        };

        const scrollToIndex = (index, behavior = "smooth") => {
            updateActiveSlides(index);
            alignActiveSlide(behavior);
        };

        prevButton.addEventListener("click", () => {
            scrollToIndex(getActiveIndex() - 1);
        });

        nextButton.addEventListener("click", () => {
            scrollToIndex(getActiveIndex() + 1);
        });

        dots.forEach((dot, index) => {
            dot.addEventListener("click", () => {
                scrollToIndex(index);
            });
        });

        track.addEventListener("scroll", requestStateUpdate, { passive: true });
        track.addEventListener("keydown", (event) => {
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                scrollToIndex(getActiveIndex() - 1);
            }

            if (event.key === "ArrowRight") {
                event.preventDefault();
                scrollToIndex(getActiveIndex() + 1);
            }
        });

        const requestResizeAlign = () => {
            if (resizeFrameId) {
                return;
            }

            resizeFrameId = window.requestAnimationFrame(() => {
                resizeFrameId = 0;
                updateTrackInset();
                alignActiveSlide("auto");
                updateCarouselState();
            });
        };

        window.addEventListener("resize", requestResizeAlign);

        if ("ResizeObserver" in window) {
            const observer = new ResizeObserver(requestResizeAlign);
            observer.observe(track);
            if (items[0]) {
                observer.observe(items[0]);
            }
        }

        updateTrackInset();
        updateActiveSlides(0);

        window.requestAnimationFrame(() => {
            alignActiveSlide("auto");
            updateCarouselState();
        });
    });
}

function initializeLessonSlideViewer() {
    document.querySelectorAll("[data-lesson-slide-viewer]").forEach((viewer) => {
        const dataId = viewer.dataset.slideDataId;
        const scriptElement = dataId ? document.getElementById(dataId) : null;
        if (!scriptElement) {
            return;
        }

        let slides = [];
        try {
            slides = JSON.parse(scriptElement.textContent || "[]");
        } catch (error) {
            slides = [];
        }

        if (!Array.isArray(slides) || !slides.length) {
            return;
        }

        const titleElement = viewer.querySelector("[data-lesson-slide-title]");
        const fileElement = viewer.querySelector("[data-lesson-slide-file]");
        const currentCounter = viewer.querySelector("[data-lesson-slide-current]");
        const totalCounter = viewer.querySelector("[data-lesson-slide-total]");
        const imageElement = viewer.querySelector("[data-lesson-slide-image]");
        const prevButton = viewer.querySelector("[data-lesson-slide-prev]");
        const nextButton = viewer.querySelector("[data-lesson-slide-next]");
        const pdfAction = viewer.querySelector("[data-lesson-slide-pdf]");
        const downloadAction = viewer.querySelector("[data-lesson-slide-download]");
        const completionRow = viewer.querySelector("[data-lesson-slide-completion]");

        let currentSlideIndex = 0;
        let lastReachedSlideIndex = 0;
        let completionUnlocked = viewer.dataset.completionUnlocked === "true";

        if (totalCounter) {
            totalCounter.textContent = `${slides.length}`;
        }

        if (pdfAction) {
            pdfAction.dataset.defaultLabel = pdfAction.textContent.trim();
        }
        if (downloadAction) {
            downloadAction.dataset.defaultLabel = downloadAction.textContent.trim();
        }

        const setButtonState = (button, disabled) => {
            if (!button) {
                return;
            }
            button.disabled = disabled;
            button.setAttribute("aria-disabled", disabled ? "true" : "false");
        };

        const setActionState = (action, url, label) => {
            if (!action) {
                return;
            }

            if (!url) {
                action.hidden = true;
                action.removeAttribute("href");
                return;
            }

            action.hidden = false;
            action.href = url;
            action.textContent = label || action.dataset.defaultLabel || action.textContent;
        };

        const revealCompletion = () => {
            if (!completionRow) {
                return;
            }

            if (!completionRow.hidden) {
                completionRow.classList.add("is-visible");
                return;
            }

            completionRow.hidden = false;
            window.requestAnimationFrame(() => {
                completionRow.classList.add("is-visible");
            });
        };

        const updateViewer = (nextIndex) => {
            currentSlideIndex = Math.max(0, Math.min(slides.length - 1, nextIndex));
            lastReachedSlideIndex = Math.max(lastReachedSlideIndex, currentSlideIndex);

            const slide = slides[currentSlideIndex];
            if (!slide) {
                return;
            }

            viewer.dataset.currentSlideIndex = `${currentSlideIndex}`;

            setText(titleElement, slide.deck_title || "Lecture presentation");
            if (fileElement) {
                fileElement.textContent = slide.file_name || "";
                fileElement.hidden = !String(slide.file_name || "").trim();
            }

            if (currentCounter) {
                currentCounter.textContent = `${currentSlideIndex + 1}`;
            }

            if (imageElement) {
                imageElement.src = slide.image_url || "";
                imageElement.alt = slide.alt || `${slide.deck_title || "Lecture presentation"} - Slide ${currentSlideIndex + 1}`;
            }

            setActionState(pdfAction, slide.pdf_url, slide.pdf_label);
            setActionState(downloadAction, slide.download_url, slide.download_label);

            setButtonState(prevButton, currentSlideIndex === 0);
            setButtonState(nextButton, currentSlideIndex === slides.length - 1);

            if (!completionUnlocked && lastReachedSlideIndex === slides.length - 1) {
                completionUnlocked = true;
                viewer.dataset.completionUnlocked = "true";
            }

            if (completionUnlocked) {
                revealCompletion();
            }
        };

        const isTypingTarget = (target) => {
            if (!(target instanceof HTMLElement)) {
                return false;
            }
            return Boolean(
                target.closest("input, textarea, select, [contenteditable='true']")
            );
        };

        if (prevButton) {
            prevButton.addEventListener("click", () => {
                if (currentSlideIndex > 0) {
                    updateViewer(currentSlideIndex - 1);
                }
            });
        }

        if (nextButton) {
            nextButton.addEventListener("click", () => {
                if (currentSlideIndex < slides.length - 1) {
                    updateViewer(currentSlideIndex + 1);
                }
            });
        }

        viewer.addEventListener("keydown", (event) => {
            if (isTypingTarget(event.target)) {
                return;
            }

            if (event.key === "ArrowLeft") {
                event.preventDefault();
                if (currentSlideIndex > 0) {
                    updateViewer(currentSlideIndex - 1);
                }
            }

            if (event.key === "ArrowRight") {
                event.preventDefault();
                if (currentSlideIndex < slides.length - 1) {
                    updateViewer(currentSlideIndex + 1);
                }
            }
        });

        updateViewer(0);
    });
}

function initializeCodeRunnerForms() {
    document.querySelectorAll("[data-code-runner-form]").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            const textarea = form.querySelector("textarea[name='response']");
            if (!textarea || textarea.disabled) {
                return;
            }

            const apiUrl = form.dataset.apiUrl;
            if (!apiUrl) {
                return;
            }

            event.preventDefault();

            const shell = form.closest("[data-code-runner-shell]");
            const submitButton = (shell && shell.querySelector("[data-runner-submit]")) || form.querySelector("[data-runner-submit]");
            setFormBusy(shell, submitButton, true);
            showRunnerPendingState(shell, submitButton);

            try {
                const response = await fetch(apiUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(form),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ response: textarea.value }),
                });

                const payload = await response.json().catch(() => ({}));

                if (!response.ok) {
                    if (payload.activity) {
                        updateRunnerUI(shell, payload);
                    } else {
                        showRunnerPanelNotification(
                            shell,
                            payload.system_notification || payload.notification || {
                                level: "error",
                                title: "Code runner request failed",
                                message: "The server could not process the code submission.",
                            },
                            {
                                statusLabel: "Request failed",
                                summaryLabel: "Status: Error",
                                summaryTone: "error",
                            },
                        );
                        maybeFocusCompilerResults(shell);
                    }
                    updateRunnerStatus(shell, "error", "Request failed");
                    return;
                }

                updateRunnerUI(shell, payload);
                if (!payload.activity && shell) {
                    showRunnerPanelNotification(
                        shell,
                        payload.system_notification || payload.notification || {
                            level: "info",
                            title: "Submission received",
                            message: "Your code has been processed.",
                        },
                        {
                            statusLabel: "Updated",
                            summaryLabel: "Status: Updated",
                            summaryTone: "neutral",
                        },
                    );
                }
            } catch (error) {
                showRunnerPanelNotification(
                    shell,
                    {
                        level: "error",
                        title: "Code runner unavailable",
                        message: "We could not connect to the code runner. Please try again.",
                    },
                    {
                        statusLabel: "Offline",
                        summaryLabel: "Status: Error",
                        summaryTone: "error",
                    },
                );
                updateRunnerStatus(shell, "error", "Offline");
                maybeFocusCompilerResults(shell);
            } finally {
                setFormBusy(shell, submitButton, false);
            }
        });
    });
}

function initializeRunnerResetButtons() {
    document.querySelectorAll("[data-runner-reset]").forEach((button) => {
        button.addEventListener("click", () => {
            const shell = button.closest("[data-code-runner-shell]");
            const textarea = shell && shell.querySelector("textarea[name='response']");
            const starterCode = readStarterCode(button.dataset.starterCodeId);

            if (!textarea || textarea.disabled || starterCode === null) {
                return;
            }

            textarea.value = starterCode;
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            resetRunnerResults(shell);
            updateRunnerStatus(shell, "ready", "Starter restored");
        });
    });
}

function setFormBusy(shell, submitButton, busy) {
    if (!submitButton) {
        return;
    }

    const textarea = shell ? shell.querySelector("textarea[name='response']") : null;
    const isValidated = textarea && textarea.disabled;

    if (busy) {
        submitButton.disabled = true;
        submitButton.textContent = submitButton.dataset.busyLabel || "Running...";
        updateRunnerStatus(shell, "running", submitButton.dataset.busyLabel || "Running...");
        return;
    }

    if (isValidated) {
        submitButton.disabled = true;
        submitButton.textContent = "Activity Validated";
        return;
    }

    submitButton.disabled = false;
    submitButton.textContent = submitButton.dataset.idleLabel || "Run Code";
}

function updateRunnerUI(shell, payload) {
    if (!shell || !payload || !payload.activity) {
        return;
    }

    const activity = payload.activity;
    const progress = payload.progress || {};
    const systemNotification = payload.system_notification || payload.notification || activity.notification || {};

    setText(shell.querySelector("[data-runner-feedback-title]"), systemNotification.title || "Feedback");
    setText(
        shell.querySelector("[data-runner-feedback-body]"),
        systemNotification.message || activity.explanation || "Feedback updated.",
    );

    const feedback = shell.querySelector("[data-runner-feedback]");
    if (feedback) {
        feedback.classList.remove("correct", "incorrect");
        feedback.classList.add(activity.validation_result === "correct" ? "correct" : "incorrect");
    }

    setText(shell.querySelector("[data-runner-output]"), activity.program_output || "");
    toggleVisibility(shell.querySelector("[data-runner-output-card]"), Boolean(activity.program_output));

    setText(shell.querySelector("[data-runner-errors]"), activity.errors || "");
    toggleVisibility(shell.querySelector("[data-runner-error-card]"), Boolean(activity.errors));

    const hintText = activity.hint || shell.querySelector("[data-runner-hint]")?.textContent || "";
    setText(shell.querySelector("[data-runner-hint]"), hintText);
    toggleVisibility(shell.querySelector("[data-runner-hint-card]"), Boolean(hintText.trim()));

    setText(shell.querySelector("[data-runner-suggestion]"), activity.learning_suggestion || "");
    toggleVisibility(shell.querySelector("[data-runner-suggestion-card]"), Boolean(activity.learning_suggestion));

    const executionTime = activity.execution_time_ms ? `${activity.execution_time_ms} ms` : "";
    setText(shell.querySelector("[data-runner-execution-time]"), executionTime);

    if (typeof progress.activity_attempts === "number") {
        setText(shell.querySelector("[data-runner-attempts]"), `Attempts: ${progress.activity_attempts}`);
    }

    updateSystemNotification(shell, systemNotification, activity);
    updateSystemDetailCard(shell, systemNotification, activity);
    updateRunnerTitles(shell, systemNotification, activity);
    updateResultsSummary(shell, activity, progress, systemNotification);
    updateConceptReview(shell, progress);

    if (progress.activity_completed) {
        const textarea = shell.querySelector("textarea[name='response']");
        const submitButton = shell.querySelector("[data-runner-submit]");
        if (textarea) {
            textarea.disabled = true;
        }
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Activity Validated";
        }
    }

    const nextStatus = deriveRunnerStatus(activity, progress, systemNotification);
    updateRunnerStatus(shell, nextStatus.tone, nextStatus.label);
    updateLessonProgress(progress, payload.next_lesson);
    maybeFocusCompilerResults(shell);
}

function showRunnerPendingState(shell, submitButton) {
    if (!shell) {
        return;
    }

    showRunnerPanelNotification(
        shell,
        {
            level: "info",
            title: submitButton?.dataset?.busyLabel || "Running code",
            message: "Your latest code is being executed. Results and backend feedback will appear below.",
            label: "Run in progress",
        },
        {
            summaryLabel: "Status: Running",
            summaryTone: "running",
        },
    );
}

function resetRunnerResults(shell) {
    if (!shell) {
        return;
    }

    const defaults = getRunnerNotificationDefaults(shell);

    setText(shell.querySelector("[data-runner-output]"), "");
    setText(shell.querySelector("[data-runner-errors]"), "");
    setText(shell.querySelector("[data-runner-suggestion]"), "");
    setText(shell.querySelector("[data-runner-execution-time]"), "");
    setText(shell.querySelector("[data-system-detail]"), "");
    setText(shell.querySelector("[data-system-detail-caption]"), shell?.dataset?.detailCaption || "Runner service output");
    toggleVisibility(shell.querySelector("[data-runner-output-card]"), false);
    toggleVisibility(shell.querySelector("[data-runner-error-card]"), false);
    toggleVisibility(shell.querySelector("[data-runner-suggestion-card]"), false);
    toggleVisibility(shell.querySelector("[data-system-detail-card]"), false);
    updateRunnerTitles(shell, {}, { details: {} });

    showRunnerPanelNotification(
        shell,
        {
            level: "info",
            title: "Starter code restored",
            message: "The editor was reset to the original lesson code. Run Code when you're ready.",
            label: "Editor update",
        },
        {
            statusLabel: "Starter restored",
            summaryLabel: "Status: Ready",
            summaryTone: "neutral",
            clearMeta: true,
        },
    );

    if (!shell.querySelector("[data-system-notification]")) {
        setText(shell.querySelector("[data-runner-feedback-title]"), defaults.title);
        setText(shell.querySelector("[data-runner-feedback-body]"), defaults.message);
    }
}

function showRunnerPanelNotification(shell, notification, options = {}) {
    if (!shell) {
        return;
    }

    const level = notification.level || options.level || "info";
    const tone = level === "info" ? "neutral" : level;
    const defaults = getRunnerNotificationDefaults(shell);
    const title = notification.title || defaults.title;
    const message = notification.message || defaults.message;
    const label = notification.label || (notification.kind ? formatNotificationKind(notification.kind) : defaults.label);

    updateRunnerFeedbackCard(shell, tone, title, message);

    const panel = shell.querySelector("[data-system-notification]");
    const kindBadge = shell.querySelector("[data-system-notification-kind]");
    if (panel) {
        panel.classList.remove("success", "error", "warning", "neutral");
        panel.classList.add(tone);
        setText(shell.querySelector("[data-system-notification-title]"), title);
        setText(shell.querySelector("[data-system-notification-message]"), message);
        setText(kindBadge, label);
        setPillTone(kindBadge, options.kindTone || tone);
        setText(
            shell.querySelector("[data-system-notification-meta]"),
            options.clearMeta ? "" : options.meta || "",
        );
    }

    if (options.summaryLabel) {
        updateResultsSummaryState(
            shell.querySelector("[data-runner-results-summary]"),
            options.summaryTone || tone,
            options.summaryLabel,
        );
    }

    if (options.statusLabel) {
        updateRunnerStatus(shell, options.statusTone || (tone === "neutral" ? "ready" : tone), options.statusLabel);
    }
}

function updateRunnerFeedbackCard(shell, tone, title, message) {
    const feedback = shell.querySelector("[data-runner-feedback]");
    if (!feedback) {
        return;
    }

    feedback.classList.remove("correct", "incorrect");
    if (tone === "success") {
        feedback.classList.add("correct");
    } else if (tone === "warning" || tone === "error") {
        feedback.classList.add("incorrect");
    }
    setText(shell.querySelector("[data-runner-feedback-title]"), title);
    setText(shell.querySelector("[data-runner-feedback-body]"), message);
}

function updateSystemNotification(shell, notification, activity) {
    const panel = shell.querySelector("[data-system-notification]");
    const kindBadge = shell.querySelector("[data-system-notification-kind]");
    if (!panel) {
        return;
    }

    const defaults = getRunnerNotificationDefaults(shell);
    const level = notification.level || (activity.execution_status === "error" ? "error" : activity.validation_result === "correct" ? "success" : "warning");
    panel.classList.remove("success", "error", "warning", "neutral");
    panel.classList.add(level === "info" ? "neutral" : level);

    setText(
        shell.querySelector("[data-system-notification-title]"),
        notification.title || defaults.title,
    );
    setText(
        shell.querySelector("[data-system-notification-message]"),
        notification.message || activity.explanation || defaults.message,
    );
    setText(
        kindBadge,
        notification.label || (notification.kind ? formatNotificationKind(notification.kind) : defaults.label),
    );
    setPillTone(kindBadge, level === "info" ? "neutral" : level);
    setText(shell.querySelector("[data-system-notification-meta]"), buildNotificationMeta(shell, notification, activity));
}

function updateResultsSummary(shell, activity, progress, notification) {
    const summary = shell.querySelector("[data-runner-results-summary]");
    if (!summary) {
        return;
    }

    const state = deriveResultsSummary(activity, progress, notification);
    updateResultsSummaryState(summary, state.tone, state.label);
}

function updateResultsSummaryState(summary, tone, label) {
    if (!summary) {
        return;
    }

    setText(summary, label);
    setPillTone(summary, tone);
}

function updateConceptReview(shell, progress) {
    const panel = shell.querySelector("[data-runner-concept-review]");
    if (!panel) {
        return;
    }

    toggleVisibility(panel, Boolean(progress.activity_completed));
}

function updateSystemDetailCard(shell, notification, activity) {
    const detail = String(notification.detail || "").trim();
    const errors = String(activity.errors || "").trim();
    const output = String(activity.program_output || "").trim();
    const shouldShow = Boolean(detail) && detail !== errors && detail !== output;
    const defaultCaption = shell?.dataset?.detailCaption || "Runner service output";
    const environmentCaption = shell?.dataset?.environmentDetailCaption || "Runtime environment output";

    setText(shell.querySelector("[data-system-detail]"), shouldShow ? detail : "");
    setText(
        shell.querySelector("[data-system-detail-caption]"),
        activity.details && activity.details.environment_issue ? environmentCaption : defaultCaption,
    );
    toggleVisibility(shell.querySelector("[data-system-detail-card]"), shouldShow);
}

function updateRunnerTitles(shell, notification, activity) {
    const errorTitle = shell.querySelector("[data-runner-error-title]");
    if (errorTitle) {
        let label = shell?.dataset?.defaultErrorTitle || "Runner Details";
        if (activity.details && activity.details.environment_issue) {
            label = shell?.dataset?.environmentErrorTitle || "Runtime Environment Details";
        } else if ((notification.kind || "").includes("runtime") || (notification.kind || "").includes("timeout")) {
            label = "Runtime Error Details";
        }
        errorTitle.textContent = label;
    }
}

function updateRunnerStatus(shell, tone, label) {
    const status = shell && shell.querySelector("[data-runner-status]");
    if (!status) {
        return;
    }

    status.classList.remove("ready", "running", "success", "error", "warning");
    status.classList.add(tone);
    status.textContent = label;
}

function deriveRunnerStatus(activity, progress, notification = {}) {
    if (progress.activity_completed) {
        return { tone: "success", label: "Validated" };
    }

    if (activity.details && activity.details.environment_issue) {
        return { tone: "error", label: "Setup issue" };
    }

    if (activity.execution_status === "error") {
        if ((notification.kind || "").includes("timeout")) {
            return { tone: "error", label: "Timed out" };
        }

        if ((notification.kind || "").includes("compile")) {
            return { tone: "error", label: "Compilation error" };
        }

        if ((notification.kind || "").includes("runtime")) {
            return { tone: "error", label: "Runtime error" };
        }

        return { tone: "error", label: "Error" };
    }

    if (activity.validation_result === "incorrect") {
        return { tone: "warning", label: "Needs changes" };
    }

    return { tone: "ready", label: "Ready" };
}

function deriveResultsSummary(activity, progress, notification = {}) {
    if (progress.activity_completed) {
        return { tone: "success", label: "Status: Success" };
    }

    if (activity.details && activity.details.environment_issue) {
        return { tone: "error", label: "Status: Setup issue" };
    }

    if (activity.execution_status === "error") {
        return { tone: "error", label: "Status: Error" };
    }

    if ((notification.kind || "").includes("validation") || activity.validation_result === "incorrect") {
        return { tone: "warning", label: "Status: Needs changes" };
    }

    return { tone: "neutral", label: "Status: Waiting" };
}

function updateLessonProgress(progress, nextLesson) {
    const activityStatus = document.querySelector("[data-activity-check-status]");
    if (activityStatus) {
        activityStatus.classList.remove("done", "open", "locked");
        activityStatus.classList.add(progress.activity_completed ? "done" : "open");
    }

    const progressPill = document.querySelector("[data-lesson-progress-pill]");
    if (progressPill) {
        progressPill.textContent = progress.lesson_completed ? "Completed" : "In Progress";
    }

    const nextLessonSlot = document.querySelector("[data-next-lesson-shortcut]");
    if (!nextLessonSlot) {
        return;
    }

    nextLessonSlot.innerHTML = "";
    if (!nextLesson) {
        return;
    }

    const link = document.createElement("a");
    link.className = "button compact";
    link.href = buildNextLessonUrl(nextLesson.slug);
    link.textContent = "Open Next Lesson";
    nextLessonSlot.appendChild(link);
}

function buildNotificationMeta(shell, notification, activity) {
    const location = notification.location || {};
    const details = activity.details || {};
    const runnerFileName = shell?.dataset?.runnerFileName || "main.txt";

    if (location.line) {
        return `${location.file || runnerFileName} line ${location.line}, column ${location.column}`;
    }

    if (details.environment_issue) {
        const issueLabel = formatEnvironmentIssue(details.environment_issue);
        const stageLabel = details.compiler_stage ? `${capitalizeLabel(details.compiler_stage)} stage` : "Compiler stage";
        if (activity.execution_time_ms) {
            return `${issueLabel} - ${stageLabel} - ${activity.execution_time_ms} ms`;
        }
        return `${issueLabel} - ${stageLabel}`;
    }

    if (activity.execution_time_ms) {
        return `${activity.execution_time_ms} ms`;
    }

    if (notification.stage) {
        return `Stage: ${notification.stage}`;
    }

    return "";
}

function formatNotificationKind(kind) {
    const labels = {
        csharp_compiler: "Compiler feedback",
        csharp_compiler_environment_error: "Setup issue",
        csharp_compile_error: "Compilation error",
        csharp_runtime_error: "Runtime error",
        csharp_success: "Run successful",
        csharp_validation_feedback: "Needs changes",
        php_runtime_unavailable: "Setup issue",
        php_timeout: "Timed out",
        php_runtime_error: "Runtime error",
        php_success: "Run successful",
        php_validation_feedback: "Needs changes",
    };
    if (labels[kind]) {
        return labels[kind];
    }

    return String(kind || "")
        .replace(/_/g, " ")
        .replace(/\bcsharp\b/gi, "C#")
        .replace(/\bphp\b/gi, "PHP")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}

function maybeFocusCompilerResults(shell) {
    if (window.innerWidth > 900 || !shell.querySelector("[data-dedicated-runner-shell], [data-csharp-compiler-shell]")) {
        return;
    }

    const target = getRunnerResultsTarget(shell);
    if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function buildNextLessonUrl(nextLessonSlug) {
    const currentUrl = new URL(window.location.href);
    const parts = currentUrl.pathname.replace(/\/$/, "").split("/");
    parts[parts.length - 1] = nextLessonSlug;
    return parts.join("/") + "/";
}

function getCsrfToken(form) {
    const formToken = form.querySelector("input[name='csrfmiddlewaretoken']");
    if (formToken) {
        return formToken.value;
    }

    const cookie = document.cookie
        .split(";")
        .map((item) => item.trim())
        .find((item) => item.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
}

function focusRunnerResults(shell) {
    const results = shell && shell.querySelector("[data-runner-results]");
    const target = getRunnerResultsTarget(shell);
    if (!results || !target || !hasMeaningfulRunnerResults(shell)) {
        return false;
    }

    results.scrollIntoView({ behavior: "smooth", block: "start" });
    target.classList.remove("result-flash");
    void target.offsetWidth;
    target.classList.add("result-flash");
    if (!target.hasAttribute("tabindex")) {
        target.setAttribute("tabindex", "-1");
    }
    target.focus({ preventScroll: true });
    window.setTimeout(() => target.classList.remove("result-flash"), 1500);
    return true;
}

function getRunnerResultsTarget(shell) {
    if (!shell) {
        return null;
    }

    return (
        shell.querySelector("[data-runner-error-card]:not([hidden])") ||
        shell.querySelector("[data-runner-output-card]:not([hidden])") ||
        shell.querySelector("[data-system-detail-card]:not([hidden])") ||
        shell.querySelector("[data-system-notification]")
    );
}

function hasMeaningfulRunnerResults(shell) {
    if (!shell) {
        return false;
    }

    const defaults = getRunnerNotificationDefaults(shell);
    const notificationTitle = shell.querySelector("[data-system-notification-title]")?.textContent?.trim() || "";
    const notificationMessage = shell.querySelector("[data-system-notification-message]")?.textContent?.trim() || "";
    const visibleOutput = shell.querySelector("[data-runner-output-card]:not([hidden])");
    const visibleErrors = shell.querySelector("[data-runner-error-card]:not([hidden])");
    const visibleDetail = shell.querySelector("[data-system-detail-card]:not([hidden])");

    return Boolean(
        visibleOutput ||
            visibleErrors ||
            visibleDetail ||
            notificationTitle !== defaults.title ||
            notificationMessage !== defaults.message,
    );
}

function getRunnerNotificationDefaults(shell) {
    return {
        title: shell?.dataset?.defaultNotificationTitle || "Code runner feedback will appear here.",
        message: shell?.dataset?.defaultNotificationMessage || "Run the code to receive backend feedback.",
        label: shell?.dataset?.defaultNotificationLabel || "Runner feedback",
    };
}

function readStarterCode(starterCodeId) {
    if (!starterCodeId) {
        return null;
    }

    const element = document.getElementById(starterCodeId);
    if (!element) {
        return null;
    }

    try {
        return JSON.parse(element.textContent || '""');
    } catch (error) {
        return null;
    }
}

function formatEnvironmentIssue(code) {
    const labels = {
        compiler_service_exception: "Compiler service issue",
        msbuild_environment: "MSBuild environment issue",
        nuget_configuration: "NuGet configuration issue",
        workload_verification: ".NET workload issue",
    };
    return labels[code] || "Compiler setup issue";
}

function capitalizeLabel(value) {
    const text = String(value || "").replace(/_/g, " ");
    return text.charAt(0).toUpperCase() + text.slice(1);
}

function setPillTone(element, tone) {
    if (!element) {
        return;
    }

    element.classList.remove("neutral", "running", "success", "warning", "error");
    element.classList.add(tone);
}

function setText(element, value) {
    if (element) {
        element.textContent = value || "";
    }
}

function toggleVisibility(element, visible) {
    if (element) {
        element.hidden = !visible;
    }
}
