document.addEventListener("DOMContentLoaded", () => {
    const toastStack = document.querySelector("[data-toast-stack]");
    const notify = createNotifier(toastStack);

    initializeExistingToasts();
    initializeCodeRunnerForms(notify);
    initializeRunnerResetButtons(notify);
    initializeViewResultsButtons(notify);
});

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

function initializeCodeRunnerForms(notify) {
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
            const submitButton = form.querySelector("[data-runner-submit]");
            setFormBusy(shell, submitButton, true);

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
                    }
                    updateRunnerStatus(shell, "error", "Request failed");
                    notify(
                        payload.system_notification || payload.notification || {
                            level: "error",
                            title: "Compiler request failed",
                            message: "The server could not process the code submission.",
                        },
                    );
                    return;
                }

                updateRunnerUI(shell, payload);
                notify(
                    payload.system_notification || payload.notification || {
                        level: "info",
                        title: "Submission received",
                        message: "Your code has been processed.",
                    },
                );
            } catch (error) {
                updateRunnerStatus(shell, "error", "Offline");
                notify({
                    level: "error",
                    title: "Compiler unavailable",
                    message: "We could not connect to the code runner. Please try again.",
                });
            } finally {
                setFormBusy(shell, submitButton, false);
            }
        });
    });
}

function initializeRunnerResetButtons(notify) {
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
            updateRunnerStatus(shell, "ready", "Starter restored");

            if (notify) {
                notify({
                    level: "info",
                    title: "Starter code restored",
                    message: "The editor was reset to the original lesson code. Compile again when you're ready.",
                });
            }
        });
    });
}

function initializeViewResultsButtons(notify) {
    document.querySelectorAll("[data-runner-view-results]").forEach((button) => {
        button.addEventListener("click", () => {
            const shell = button.closest("[data-code-runner-shell]");
            if (!focusRunnerResults(shell) && notify) {
                notify({
                    level: "info",
                    title: "No results yet",
                    message: "Compile and run the code first, then open the results panel.",
                });
            }
        });
    });
}

function setFormBusy(shell, submitButton, busy) {
    if (!submitButton) {
        return;
    }

    const textarea = shell.querySelector("textarea[name='response']");
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
    submitButton.textContent = submitButton.dataset.idleLabel || "Run and Check Code";
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

function updateSystemNotification(shell, notification, activity) {
    const panel = shell.querySelector("[data-system-notification]");
    const kindBadge = shell.querySelector("[data-system-notification-kind]");
    if (!panel) {
        return;
    }

    const level = notification.level || (activity.execution_status === "error" ? "error" : activity.validation_result === "correct" ? "success" : "warning");
    panel.classList.remove("success", "error", "warning", "neutral");
    panel.classList.add(level === "info" ? "neutral" : level);

    setText(
        shell.querySelector("[data-system-notification-title]"),
        notification.title || "C# compiler feedback will appear here.",
    );
    setText(
        shell.querySelector("[data-system-notification-message]"),
        notification.message || activity.explanation || "Compile the code to receive backend compiler feedback.",
    );
    setText(
        kindBadge,
        notification.label || formatNotificationKind(notification.kind || "csharp_compiler"),
    );
    setPillTone(kindBadge, level === "info" ? "neutral" : level);
    setText(shell.querySelector("[data-system-notification-meta]"), buildNotificationMeta(notification, activity));
}

function updateResultsSummary(shell, activity, progress, notification) {
    const summary = shell.querySelector("[data-runner-results-summary]");
    if (!summary) {
        return;
    }

    const state = deriveResultsSummary(activity, progress, notification);
    setText(summary, state.label);
    setPillTone(summary, state.tone);
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

    setText(shell.querySelector("[data-system-detail]"), shouldShow ? detail : "");
    setText(
        shell.querySelector("[data-system-detail-caption]"),
        activity.details && activity.details.environment_issue ? "Compiler environment output" : "Compiler service output",
    );
    toggleVisibility(shell.querySelector("[data-system-detail-card]"), shouldShow);
}

function updateRunnerTitles(shell, notification, activity) {
    const errorTitle = shell.querySelector("[data-runner-error-title]");
    if (errorTitle) {
        let label = "Compiler Details";
        if (activity.details && activity.details.environment_issue) {
            label = "Compiler Environment Details";
        } else if ((notification.kind || "").includes("runtime")) {
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
        return { tone: "error", label: "Compiler setup issue" };
    }

    if (activity.execution_status === "error") {
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

function buildNotificationMeta(notification, activity) {
    const location = notification.location || {};
    const details = activity.details || {};

    if (location.line) {
        return `${location.file || "Program.cs"} line ${location.line}, column ${location.column}`;
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
    };
    if (labels[kind]) {
        return labels[kind];
    }

    return String(kind || "")
        .replace(/_/g, " ")
        .replace(/\bcsharp\b/gi, "C#")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}

function maybeFocusCompilerResults(shell) {
    if (window.innerWidth > 900 || !shell.querySelector("[data-csharp-compiler-shell]")) {
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

    const notificationTitle = shell.querySelector("[data-system-notification-title]")?.textContent?.trim() || "";
    const notificationMessage = shell.querySelector("[data-system-notification-message]")?.textContent?.trim() || "";
    const defaultTitle = "C# compiler feedback will appear here.";
    const defaultMessage =
        "Use Run to compile the current C# program. The backend compiler service will generate the notification you see here.";
    const visibleOutput = shell.querySelector("[data-runner-output-card]:not([hidden])");
    const visibleErrors = shell.querySelector("[data-runner-error-card]:not([hidden])");
    const visibleDetail = shell.querySelector("[data-system-detail-card]:not([hidden])");

    return Boolean(
        visibleOutput ||
            visibleErrors ||
            visibleDetail ||
            notificationTitle !== defaultTitle ||
            notificationMessage !== defaultMessage,
    );
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

    element.classList.remove("neutral", "success", "warning", "error");
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
