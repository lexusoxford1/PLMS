const API_BASE = "/admin-panel/api";

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function getCookie(name) {
    const cookie = document.cookie
        .split(";")
        .map((entry) => entry.trim())
        .find((entry) => entry.startsWith(`${name}=`));
    return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

function extractErrorMessage(payload) {
    if (!payload) {
        return "Something went wrong.";
    }
    if (payload.detail) {
        return payload.detail;
    }
    if (payload.errors) {
        return Object.values(payload.errors)
            .flat()
            .join(" ");
    }
    return "Something went wrong.";
}

async function request(url, options = {}) {
    const config = { credentials: "same-origin", ...options };
    const headers = new Headers(config.headers || {});
    if (!(config.body instanceof FormData) && config.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }
    if ((config.method || "GET").toUpperCase() !== "GET") {
        headers.set("X-CSRFToken", getCookie("csrftoken"));
    }
    headers.set("X-Requested-With", "XMLHttpRequest");
    config.headers = headers;

    const response = await fetch(url, config);
    let payload = {};
    try {
        payload = await response.json();
    } catch (error) {
        payload = {};
    }

    if (response.status === 401 && payload.login_url) {
        const next = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
        window.location.href = `${payload.login_url}?next=${next}`;
        throw new Error("Your admin session has expired. Please sign in again.");
    }

    if (!response.ok) {
        throw new Error(extractErrorMessage(payload));
    }
    return payload;
}

function setFeedback(element, message, tone = "info") {
    if (!element) {
        return;
    }
    if (!message) {
        element.hidden = true;
        element.textContent = "";
        element.dataset.tone = "";
        return;
    }
    element.hidden = false;
    element.textContent = message;
    element.dataset.tone = tone;
}

function renderEmpty(container, message) {
    container.innerHTML = `<div class="admin-empty-state"><p>${escapeHtml(message)}</p></div>`;
}

function fillSelect(select, items, { blankLabel = "", valueKey = "id", labelKey = "title" } = {}) {
    if (!select) {
        return;
    }
    const options = [];
    if (blankLabel) {
        options.push(`<option value="">${escapeHtml(blankLabel)}</option>`);
    }
    options.push(
        ...items.map(
            (item) => `<option value="${escapeHtml(item[valueKey])}">${escapeHtml(item[labelKey])}</option>`
        )
    );
    select.innerHTML = options.join("");
}

function formatDate(value) {
    if (!value) {
        return "";
    }
    try {
        return new Intl.DateTimeFormat("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        }).format(new Date(value));
    } catch (error) {
        return value;
    }
}

function createMetricCard(label, value, helper = "") {
    return `
        <article class="admin-metric-card">
            <span class="admin-metric-card__label">${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
            <p>${escapeHtml(helper)}</p>
        </article>
    `;
}

function createProgressBar(value) {
    return `
        <div class="admin-progress">
            <strong>${escapeHtml(value)}%</strong>
            <div class="admin-progress__bar"><span style="width: ${Math.max(0, Math.min(100, value))}%;"></span></div>
        </div>
    `;
}

function setupRichEditors(scope = document) {
    scope.querySelectorAll("[data-rich-editor]").forEach((editor) => {
        if (editor.dataset.bound === "true") {
            return;
        }
        const surface = editor.querySelector("[data-rich-surface]");
        const input = editor.querySelector("[data-rich-input]");
        if (!surface || !input) {
            return;
        }

        const syncToInput = () => {
            input.value = surface.innerHTML.trim();
        };

        if (input.value && !surface.innerHTML.trim()) {
            surface.innerHTML = input.value;
        }

        editor.addEventListener("click", (event) => {
            const button = event.target.closest("[data-rich-command]");
            if (!button) {
                return;
            }
            event.preventDefault();
            const command = button.dataset.richCommand;
            const value = button.dataset.richValue || null;
            surface.focus();
            document.execCommand(command, false, value);
            syncToInput();
        });

        surface.addEventListener("input", syncToInput);
        editor.dataset.bound = "true";
    });
}

function buildCourseListItem(item, type = "course") {
    const meta = [];
    if (item.category_label) meta.push(item.category_label);
    if (item.difficulty_label) meta.push(item.difficulty_label);
    if (item.lesson_count !== undefined && item.lesson_count !== null) meta.push(`${item.lesson_count} lectures`);
    if (item.enrollment_count !== undefined && item.enrollment_count !== null) meta.push(`${item.enrollment_count} enrollments`);
    return `
        <button type="button" class="admin-list__item" data-${type}-item="${item.id}">
            <span class="admin-list__title">${escapeHtml(item.title || item.name)}</span>
            <span class="admin-list__meta">${escapeHtml(item.description || item.course_title || "")}</span>
            <span class="admin-list__submeta">${meta.map((value) => `<span>${escapeHtml(value)}</span>`).join("")}</span>
        </button>
    `;
}

async function loadLookups(courseId = "") {
    const query = courseId ? `?course=${encodeURIComponent(courseId)}` : "";
    return request(`${API_BASE}/lookups/${query}`);
}

async function initDashboardPage(root) {
    const metricsEl = root.querySelector("[data-dashboard-metrics]");
    const coursesEl = root.querySelector("[data-dashboard-courses]");
    const activityEl = root.querySelector("[data-dashboard-activity]");
    const data = await request(`${API_BASE}/dashboard/`);

    metricsEl.innerHTML = [
        createMetricCard("Total users", data.metrics.total_users, "Registered learners and admins"),
        createMetricCard("Active users", data.metrics.active_users, "Seen within the last 24 hours"),
        createMetricCard("Online now", data.metrics.online_users, "Seen within the last 5 minutes"),
        createMetricCard("Courses", data.metrics.total_courses, "Tracks currently managed"),
        createMetricCard("Enrollments", data.metrics.total_enrollments, "Across all courses"),
        createMetricCard("Completion rate", `${data.metrics.completion_rate}%`, "Completed enrollments"),
    ].join("");

    if (!data.course_cards.length) {
        renderEmpty(coursesEl, "No courses are available yet.");
    } else {
        coursesEl.innerHTML = data.course_cards
            .map(
                (item) => `
                    <article class="admin-mini-card">
                        <span class="admin-mini-card__label">${escapeHtml(item.title)}</span>
                        <strong>${escapeHtml(item.enrollment_count ?? 0)} learners</strong>
                        <p>${escapeHtml(item.category_label)} / ${escapeHtml(item.lesson_count ?? 0)} lectures / ${escapeHtml(item.difficulty_label)}</p>
                    </article>
                `
            )
            .join("");
    }

    activityEl.innerHTML = [
        {
            label: "New enrollments",
            items: data.recent_activity.enrollments,
            formatter: (item) => `${item.user_name} joined ${item.course_title}`,
        },
        {
            label: "Badge unlocks",
            items: data.recent_activity.badges,
            formatter: (item) => `${item.user_name} earned ${item.badge_name}`,
        },
        {
            label: "Certificates",
            items: data.recent_activity.certificates,
            formatter: (item) => `${item.user_name} completed ${item.course_title}`,
        },
    ]
        .map(
            (group) => `
                <article class="admin-feed-group">
                    <span class="admin-card__eyebrow">${escapeHtml(group.label)}</span>
                    ${
                        group.items.length
                            ? group.items
                                  .map(
                                      (item) => `
                                          <div class="admin-feed-item">
                                              <strong>${escapeHtml(group.formatter(item))}</strong>
                                              <span>${escapeHtml(item.timestamp)}</span>
                                          </div>
                                      `
                                  )
                                  .join("")
                            : `<div class="admin-empty-state"><p>No recent ${escapeHtml(group.label.toLowerCase())}.</p></div>`
                    }
                </article>
            `
        )
        .join("");
}

async function initCoursesPage(root) {
    const listEl = root.querySelector("[data-course-list]");
    const form = root.querySelector("[data-course-form]");
    const feedback = root.querySelector("[data-course-feedback]");
    const titleEl = root.querySelector("[data-course-form-title]");
    const metaEl = root.querySelector("[data-course-meta]");
    const deleteButton = root.querySelector('[data-action="delete-course"]');
    let currentId = "";
    let items = [];

    async function loadCourses(selectedId = currentId) {
        const data = await request(`${API_BASE}/courses/`);
        items = data.items;
        if (!items.length) {
            renderEmpty(listEl, "No courses yet. Create the first programming track.");
            return;
        }
        listEl.innerHTML = items.map((item) => buildCourseListItem(item)).join("");
        currentId = selectedId;
        Array.from(listEl.querySelectorAll("[data-course-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.courseItem === String(currentId));
        });
    }

    function resetForm() {
        currentId = "";
        form.reset();
        form.elements.course_id.value = "";
        form.elements.estimated_hours.value = 1;
        form.elements.is_published.checked = true;
        titleEl.textContent = "New course";
        metaEl.textContent = "";
        deleteButton.hidden = true;
        setFeedback(feedback, "");
        Array.from(listEl.querySelectorAll("[data-course-item]")).forEach((button) => button.classList.remove("is-active"));
    }

    function populateForm(item) {
        currentId = item.id;
        form.elements.course_id.value = item.id;
        form.elements.title.value = item.title || "";
        form.elements.category.value = item.category || "general";
        form.elements.description.value = item.description || "";
        form.elements.overview.value = item.overview || "";
        form.elements.difficulty.value = item.difficulty || "beginner";
        form.elements.estimated_hours.value = item.estimated_hours || 1;
        form.elements.is_published.checked = Boolean(item.is_published);
        titleEl.textContent = item.title;
        metaEl.textContent = `${item.lesson_count ?? 0} lectures / ${item.enrollment_count ?? 0} enrollments`;
        deleteButton.hidden = false;
        Array.from(listEl.querySelectorAll("[data-course-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.courseItem === String(item.id));
        });
    }

    listEl.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-course-item]");
        if (!button) {
            return;
        }
        const data = await request(`${API_BASE}/courses/${button.dataset.courseItem}/`);
        populateForm(data.item);
    });

    root.querySelector('[data-action="new-course"]').addEventListener("click", resetForm);
    root.querySelector('[data-action="reset-course"]').addEventListener("click", resetForm);
    root.querySelector('[data-action="refresh-courses"]').addEventListener("click", () => loadCourses());

    deleteButton.addEventListener("click", async () => {
        if (!currentId || !window.confirm("Delete this course and its related content?")) {
            return;
        }
        await request(`${API_BASE}/courses/${currentId}/`, { method: "DELETE" });
        resetForm();
        await loadCourses();
        setFeedback(feedback, "Course deleted successfully.", "success");
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const id = form.elements.course_id.value;
        const endpoint = id ? `${API_BASE}/courses/${id}/` : `${API_BASE}/courses/`;
        const data = await request(endpoint, { method: "POST", body: new FormData(form) });
        populateForm(data.item);
        await loadCourses(data.item.id);
        setFeedback(feedback, data.message, "success");
    });

    await loadCourses();
    resetForm();
}

async function initLecturesPage(root) {
    setupRichEditors(root);
    const listEl = root.querySelector("[data-lecture-list]");
    const form = root.querySelector("[data-lecture-form]");
    const feedback = root.querySelector("[data-lecture-feedback]");
    const titleEl = root.querySelector("[data-lecture-form-title]");
    const deleteButton = root.querySelector('[data-action="delete-lecture"]');
    const filterCourse = root.querySelector("[data-lecture-filter-course]");
    const courseSelect = root.querySelector("[data-lecture-course]");
    const editorInput = form.querySelector("[data-rich-input]");
    const editorSurface = form.querySelector("[data-rich-surface]");
    let currentId = "";

    async function refreshLookups(selectedCourseId = "") {
        const lookupData = await loadLookups();
        fillSelect(filterCourse, lookupData.courses, { blankLabel: "All courses" });
        fillSelect(courseSelect, lookupData.courses);
        if (selectedCourseId) {
            filterCourse.value = String(selectedCourseId);
            courseSelect.value = String(selectedCourseId);
        }
    }

    async function loadLectures() {
        const query = filterCourse.value ? `?course=${encodeURIComponent(filterCourse.value)}` : "";
        const data = await request(`${API_BASE}/lectures/${query}`);
        if (!data.items.length) {
            renderEmpty(listEl, "No lectures match the current course filter.");
            return;
        }
        listEl.innerHTML = data.items
            .map(
                (item) => `
                    <button type="button" class="admin-list__item" data-lecture-item="${item.id}">
                        <span class="admin-list__title">${escapeHtml(item.title)}</span>
                        <span class="admin-list__meta">${escapeHtml(item.course_title)} / Lecture ${escapeHtml(item.order)}</span>
                        <span class="admin-list__submeta">
                            <span>${escapeHtml(item.material_count ?? 0)} materials</span>
                            <span>${item.has_activity ? "Activity" : "Lecture only"}</span>
                            <span>${item.has_quiz ? "Quiz" : "No quiz"}</span>
                        </span>
                    </button>
                `
            )
            .join("");
        Array.from(listEl.querySelectorAll("[data-lecture-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.lectureItem === String(currentId));
        });
    }

    function resetForm() {
        currentId = "";
        form.reset();
        form.elements.lecture_id.value = "";
        form.elements.order.value = 1;
        form.elements.is_published.checked = true;
        editorInput.value = "";
        editorSurface.innerHTML = "";
        deleteButton.hidden = true;
        titleEl.textContent = "New lecture";
        setFeedback(feedback, "");
        Array.from(listEl.querySelectorAll("[data-lecture-item]")).forEach((button) => button.classList.remove("is-active"));
    }

    function populateForm(item) {
        currentId = item.id;
        form.elements.lecture_id.value = item.id;
        form.elements.course.value = item.course_id;
        form.elements.title.value = item.title || "";
        form.elements.order.value = item.order || 1;
        form.elements.summary.value = item.summary || "";
        form.elements.is_published.checked = Boolean(item.is_published);
        editorInput.value = item.lecture_content || "";
        editorSurface.innerHTML = item.lecture_content || "";
        titleEl.textContent = item.title;
        deleteButton.hidden = false;
        Array.from(listEl.querySelectorAll("[data-lecture-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.lectureItem === String(item.id));
        });
    }

    filterCourse.addEventListener("change", loadLectures);

    listEl.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-lecture-item]");
        if (!button) {
            return;
        }
        const data = await request(`${API_BASE}/lectures/${button.dataset.lectureItem}/`);
        populateForm(data.item);
    });

    root.querySelector('[data-action="new-lecture"]').addEventListener("click", resetForm);
    root.querySelector('[data-action="reset-lecture"]').addEventListener("click", resetForm);

    deleteButton.addEventListener("click", async () => {
        if (!currentId || !window.confirm("Delete this lecture and its linked materials?")) {
            return;
        }
        await request(`${API_BASE}/lectures/${currentId}/`, { method: "DELETE" });
        resetForm();
        await loadLectures();
        setFeedback(feedback, "Lecture deleted successfully.", "success");
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        editorInput.value = editorSurface.innerHTML.trim();
        const id = form.elements.lecture_id.value;
        const endpoint = id ? `${API_BASE}/lectures/${id}/` : `${API_BASE}/lectures/`;
        const data = await request(endpoint, { method: "POST", body: new FormData(form) });
        populateForm(data.item);
        await loadLectures();
        setFeedback(feedback, data.message, "success");
    });

    await refreshLookups();
    await loadLectures();
    resetForm();
}

async function initMaterialsPage(root) {
    const listEl = root.querySelector("[data-material-list]");
    const form = root.querySelector("[data-material-form]");
    const feedback = root.querySelector("[data-material-feedback]");
    const titleEl = root.querySelector("[data-material-form-title]");
    const deleteButton = root.querySelector('[data-action="delete-material"]');
    const filterCourse = root.querySelector("[data-material-filter-course]");
    const formCourse = root.querySelector("[data-material-course-select]");
    const formLecture = root.querySelector("[data-material-lecture-select]");
    let currentId = "";
    let lookups = { courses: [], lectures: [] };

    function filterLectures(courseId) {
        return lookups.lectures.filter((lecture) => !courseId || String(lecture.course_id) === String(courseId));
    }

    function fillLectureSelect(select, courseId, selectedLectureId = "") {
        const lectures = filterLectures(courseId);
        fillSelect(select, lectures, { blankLabel: "Select lecture", labelKey: "label" });
        if (selectedLectureId) {
            select.value = String(selectedLectureId);
        }
    }

    async function refreshLookups() {
        lookups = await loadLookups();
        fillSelect(filterCourse, lookups.courses, { blankLabel: "All courses" });
        fillSelect(formCourse, lookups.courses, { blankLabel: "Select course" });
        fillLectureSelect(formLecture, "");
    }

    async function loadMaterials() {
        const query = filterCourse.value ? `?course=${encodeURIComponent(filterCourse.value)}` : "";
        const data = await request(`${API_BASE}/materials/${query}`);
        if (!data.items.length) {
            renderEmpty(listEl, "No materials match the current filter.");
            return;
        }
        listEl.innerHTML = data.items
            .map(
                (item) => `
                    <button type="button" class="admin-list__item" data-material-item="${item.id}">
                        <span class="admin-list__title">${escapeHtml(item.title)}</span>
                        <span class="admin-list__meta">${escapeHtml(item.course_title)} / ${escapeHtml(item.lesson_title)}</span>
                        <span class="admin-list__submeta">
                            <span>${escapeHtml(item.material_type_label)}</span>
                            <span>${escapeHtml(item.file_name)}</span>
                        </span>
                    </button>
                `
            )
            .join("");
        Array.from(listEl.querySelectorAll("[data-material-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.materialItem === String(currentId));
        });
    }

    function resetForm() {
        currentId = "";
        form.reset();
        form.elements.material_id.value = "";
        titleEl.textContent = "New material";
        deleteButton.hidden = true;
        fillLectureSelect(formLecture, formCourse.value);
        setFeedback(feedback, "");
        Array.from(listEl.querySelectorAll("[data-material-item]")).forEach((button) => button.classList.remove("is-active"));
    }

    function populateForm(item) {
        currentId = item.id;
        form.elements.material_id.value = item.id;
        form.elements.title.value = item.title || "";
        form.elements.description.value = item.description || "";
        form.elements.material_type.value = item.material_type || "document";
        formCourse.value = item.course_id || "";
        fillLectureSelect(formLecture, item.course_id, item.lesson_id);
        titleEl.textContent = item.title;
        deleteButton.hidden = false;
        Array.from(listEl.querySelectorAll("[data-material-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.materialItem === String(item.id));
        });
    }

    filterCourse.addEventListener("change", loadMaterials);
    formCourse.addEventListener("change", () => fillLectureSelect(formLecture, formCourse.value));

    listEl.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-material-item]");
        if (!button) {
            return;
        }
        const data = await request(`${API_BASE}/materials/${button.dataset.materialItem}/`);
        populateForm(data.item);
    });

    root.querySelector('[data-action="new-material"]').addEventListener("click", resetForm);
    root.querySelector('[data-action="reset-material"]').addEventListener("click", resetForm);

    deleteButton.addEventListener("click", async () => {
        if (!currentId || !window.confirm("Delete this learning material?")) {
            return;
        }
        await request(`${API_BASE}/materials/${currentId}/`, { method: "DELETE" });
        resetForm();
        await loadMaterials();
        setFeedback(feedback, "Material deleted successfully.", "success");
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const id = form.elements.material_id.value;
        const endpoint = id ? `${API_BASE}/materials/${id}/` : `${API_BASE}/materials/`;
        const data = await request(endpoint, { method: "POST", body: new FormData(form) });
        populateForm(data.item);
        await loadMaterials();
        setFeedback(feedback, data.message, "success");
    });

    await refreshLookups();
    await loadMaterials();
    resetForm();
}

function createRuleCard(rule = {}) {
    return `
        <div class="admin-rule" data-rule-item data-rule-id="${escapeHtml(rule.id || "")}">
            <div class="admin-rule__grid">
                <label class="admin-form-grid__full">
                    <span>Pattern</span>
                    <input type="text" data-field="pattern" value="${escapeHtml(rule.pattern || "")}">
                </label>
                <label class="admin-form-grid__full">
                    <span>Description</span>
                    <input type="text" data-field="description" value="${escapeHtml(rule.description || "")}">
                </label>
                <label>
                    <span>Count</span>
                    <input type="number" min="1" data-field="count" value="${escapeHtml(rule.count || 1)}">
                </label>
                <label class="admin-toggle">
                    <input type="checkbox" data-field="case_sensitive" ${rule.case_sensitive ? "checked" : ""}>
                    <span>Case sensitive</span>
                </label>
            </div>
            <button type="button" class="admin-button admin-button--ghost" data-action="remove-rule">Remove rule</button>
        </div>
    `;
}

function createChoiceCard(choice = {}) {
    return `
        <div class="admin-choice" data-choice-item data-choice-id="${escapeHtml(choice.id || "")}">
            <div class="admin-choice__grid">
                <label>
                    <span>Choice text</span>
                    <input type="text" data-field="text" value="${escapeHtml(choice.text || "")}">
                </label>
                <label class="admin-toggle">
                    <input type="checkbox" data-field="is_correct" ${choice.is_correct ? "checked" : ""}>
                    <span>Correct choice</span>
                </label>
            </div>
            <button type="button" class="admin-button admin-button--ghost" data-action="remove-choice">Remove choice</button>
        </div>
    `;
}

function createQuestionCard(question = {}) {
    const isShortText = question.question_type === "short_text";
    return `
        <article class="admin-question" data-question-item data-question-id="${escapeHtml(question.id || "")}">
            <div class="admin-question__grid">
                <label class="admin-form-grid__full">
                    <span>Question prompt</span>
                    <textarea data-field="prompt" rows="3">${escapeHtml(question.prompt || "")}</textarea>
                </label>
                <label>
                    <span>Question type</span>
                    <select data-field="question_type">
                        <option value="multiple_choice" ${isShortText ? "" : "selected"}>Multiple choice</option>
                        <option value="short_text" ${isShortText ? "selected" : ""}>Short answer</option>
                    </select>
                </label>
                <label>
                    <span>Points</span>
                    <input type="number" min="1" data-field="points" value="${escapeHtml(question.points || 1)}">
                </label>
                <label class="admin-form-grid__full" data-short-answer-field ${isShortText ? "" : "hidden"}>
                    <span>Correct short answer</span>
                    <input type="text" data-field="correct_text" value="${escapeHtml(question.correct_text || "")}">
                </label>
            </div>
            <div data-choice-section ${isShortText ? "hidden" : ""}>
                <div class="admin-builder__header">
                    <h4>Choices</h4>
                    <button type="button" class="admin-button admin-button--ghost" data-action="add-choice">Add choice</button>
                </div>
                <div class="admin-choice-list" data-choice-list>
                    ${(question.choices || []).map((choice) => createChoiceCard(choice)).join("")}
                </div>
            </div>
            <button type="button" class="admin-button admin-button--ghost" data-action="remove-question">Remove question</button>
        </article>
    `;
}

async function initActivitiesPage(root) {
    const listEl = root.querySelector("[data-activity-list]");
    const filterCourse = root.querySelector("[data-activity-filter-course]");
    const form = root.querySelector("[data-activity-form]");
    const feedback = root.querySelector("[data-activity-feedback]");
    const titleEl = root.querySelector("[data-activity-form-title]");
    const requiredRulesEl = root.querySelector("[data-required-rules]");
    const forbiddenRulesEl = root.querySelector("[data-forbidden-rules]");
    const questionListEl = root.querySelector("[data-question-list]");
    const validatorType = root.querySelector("[data-validator-type]");
    const quizToggle = root.querySelector("[data-quiz-toggle]");
    const quizFields = root.querySelector("[data-quiz-fields]");
    let currentId = "";

    function syncActivityUi() {
        const isCodeRunner = validatorType.value === "code_runner";
        root.querySelectorAll("[data-code-runner-field]").forEach((field) => {
            field.hidden = !isCodeRunner;
        });
        quizFields.hidden = !quizToggle.checked;
    }

    function collectRules(container) {
        return Array.from(container.querySelectorAll("[data-rule-item]"))
            .map((card) => ({
                pattern: card.querySelector('[data-field="pattern"]').value.trim(),
                description: card.querySelector('[data-field="description"]').value.trim(),
                count: Number(card.querySelector('[data-field="count"]').value || 1),
                case_sensitive: card.querySelector('[data-field="case_sensitive"]').checked,
            }))
            .filter((rule) => rule.pattern);
    }

    function syncQuestionCard(card) {
        const type = card.querySelector('[data-field="question_type"]').value;
        card.querySelector("[data-short-answer-field]").hidden = type !== "short_text";
        card.querySelector("[data-choice-section]").hidden = type === "short_text";
    }

    function collectQuestions() {
        return Array.from(questionListEl.querySelectorAll("[data-question-item]")).map((card) => {
            const questionType = card.querySelector('[data-field="question_type"]').value;
            const question = {
                id: Number(card.dataset.questionId) || null,
                prompt: card.querySelector('[data-field="prompt"]').value.trim(),
                question_type: questionType,
                points: Number(card.querySelector('[data-field="points"]').value || 1),
                correct_text: card.querySelector('[data-field="correct_text"]')?.value.trim() || "",
                choices: [],
            };
            if (questionType === "multiple_choice") {
                question.choices = Array.from(card.querySelectorAll("[data-choice-item]")).map((choiceCard) => ({
                    id: Number(choiceCard.dataset.choiceId) || null,
                    text: choiceCard.querySelector('[data-field="text"]').value.trim(),
                    is_correct: choiceCard.querySelector('[data-field="is_correct"]').checked,
                }));
            }
            return question;
        });
    }

    function resetForm() {
        currentId = "";
        form.reset();
        form.elements.lecture_id.value = "";
        titleEl.textContent = "Select a lecture";
        requiredRulesEl.innerHTML = "";
        forbiddenRulesEl.innerHTML = "";
        questionListEl.innerHTML = "";
        root.querySelector('[name="timeout_seconds"]').value = 5;
        root.querySelector('[name="min_output_lines"]').value = 0;
        root.querySelector('[name="quiz_passing_score"]').value = 70;
        root.querySelector('[name="quiz_max_attempts"]').value = 0;
        root.querySelector('[name="ignore_whitespace"]').checked = true;
        root.querySelector('[name="quiz_is_published"]').checked = true;
        setFeedback(feedback, "");
        syncActivityUi();
        Array.from(listEl.querySelectorAll("[data-activity-item]")).forEach((button) => button.classList.remove("is-active"));
    }

    async function loadActivityList() {
        const query = filterCourse.value ? `?course=${encodeURIComponent(filterCourse.value)}` : "";
        const data = await request(`${API_BASE}/activities/${query}`);
        if (!data.items.length) {
            renderEmpty(listEl, "No lectures found for the current filter.");
            return;
        }
        listEl.innerHTML = data.items
            .map(
                (item) => `
                    <button type="button" class="admin-list__item" data-activity-item="${item.id}">
                        <span class="admin-list__title">${escapeHtml(item.title)}</span>
                        <span class="admin-list__meta">${escapeHtml(item.course_title)} / Lecture ${escapeHtml(item.order)}</span>
                        <span class="admin-list__submeta">
                            <span>${item.has_activity ? "Activity" : "No activity"}</span>
                            <span>${escapeHtml(item.validator_type)}</span>
                            <span>${item.has_quiz ? `${escapeHtml(item.question_count)} questions` : "No quiz"}</span>
                        </span>
                    </button>
                `
            )
            .join("");
        Array.from(listEl.querySelectorAll("[data-activity-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.activityItem === String(currentId));
        });
    }

    function populateForm(payload) {
        currentId = payload.lesson.id;
        form.elements.lecture_id.value = payload.lesson.id;
        titleEl.textContent = `${payload.lesson.course_title} / ${payload.lesson.title}`;
        form.elements.activity_title.value = payload.activity.activity_title || "";
        form.elements.activity_instructions.value = payload.activity.activity_instructions || "";
        form.elements.activity_hint.value = payload.activity.activity_hint || "";
        form.elements.validator_type.value = payload.activity.validator_type || "pattern";
        form.elements.language.value = payload.activity.language || "";
        form.elements.starter_code.value = payload.activity.starter_code || "";
        form.elements.expected_output.value = payload.activity.expected_output || "";
        form.elements.expected_output_contains_text.value = (payload.activity.expected_output_contains || []).join("\n");
        form.elements.output_comparison.value = payload.activity.output_comparison || "exact";
        form.elements.timeout_seconds.value = payload.activity.timeout_seconds || 5;
        form.elements.ignore_case.checked = Boolean(payload.activity.ignore_case);
        form.elements.ignore_whitespace.checked = Boolean(payload.activity.ignore_whitespace);
        form.elements.accept_alternative_solutions.checked = Boolean(payload.activity.accept_alternative_solutions);
        form.elements.min_output_lines.value = payload.activity.min_output_lines || 0;
        form.elements.success_explanation.value = payload.activity.success_explanation || "";
        form.elements.failure_hint.value = payload.activity.failure_hint || "";
        requiredRulesEl.innerHTML = (payload.activity.required_patterns || []).map((rule) => createRuleCard(rule)).join("");
        forbiddenRulesEl.innerHTML = (payload.activity.forbidden_patterns || []).map((rule) => createRuleCard(rule)).join("");

        quizToggle.checked = Boolean(payload.quiz.enabled);
        form.elements.quiz_title.value = payload.quiz.title || "";
        form.elements.quiz_instructions.value = payload.quiz.instructions || "";
        form.elements.quiz_passing_score.value = payload.quiz.passing_score || 70;
        form.elements.quiz_max_attempts.value = payload.quiz.max_attempts || 0;
        form.elements.quiz_is_published.checked = Boolean(payload.quiz.is_published);
        questionListEl.innerHTML = (payload.quiz.questions || []).map((question) => createQuestionCard(question)).join("");
        questionListEl.querySelectorAll("[data-question-item]").forEach(syncQuestionCard);
        syncActivityUi();
        Array.from(listEl.querySelectorAll("[data-activity-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.activityItem === String(currentId));
        });
    }

    filterCourse.addEventListener("change", loadActivityList);
    validatorType.addEventListener("change", syncActivityUi);
    quizToggle.addEventListener("change", syncActivityUi);

    listEl.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-activity-item]");
        if (!button) {
            return;
        }
        const data = await request(`${API_BASE}/activities/${button.dataset.activityItem}/`);
        populateForm(data.item);
    });

    root.addEventListener("click", (event) => {
        const action = event.target.closest("[data-action]")?.dataset.action;
        if (!action) {
            return;
        }
        if (action === "add-required-rule") {
            requiredRulesEl.insertAdjacentHTML("beforeend", createRuleCard());
        }
        if (action === "add-forbidden-rule") {
            forbiddenRulesEl.insertAdjacentHTML("beforeend", createRuleCard());
        }
        if (action === "remove-rule") {
            event.target.closest("[data-rule-item]")?.remove();
        }
        if (action === "add-question") {
            questionListEl.insertAdjacentHTML("beforeend", createQuestionCard());
        }
        if (action === "remove-question") {
            event.target.closest("[data-question-item]")?.remove();
        }
        if (action === "add-choice") {
            const question = event.target.closest("[data-question-item]");
            question.querySelector("[data-choice-list]").insertAdjacentHTML("beforeend", createChoiceCard());
        }
        if (action === "remove-choice") {
            event.target.closest("[data-choice-item]")?.remove();
        }
    });

    questionListEl.addEventListener("change", (event) => {
        const card = event.target.closest("[data-question-item]");
        if (card && event.target.matches('[data-field="question_type"]')) {
            syncQuestionCard(card);
        }
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.elements.lecture_id.value) {
            setFeedback(feedback, "Select a lecture before saving assessment settings.", "error");
            return;
        }
        const payload = {
            activity_title: form.elements.activity_title.value.trim(),
            activity_instructions: form.elements.activity_instructions.value.trim(),
            activity_hint: form.elements.activity_hint.value.trim(),
            validator_type: form.elements.validator_type.value,
            language: form.elements.language.value,
            starter_code: form.elements.starter_code.value,
            expected_output: form.elements.expected_output.value,
            expected_output_contains: form.elements.expected_output_contains_text.value
                .split("\n")
                .map((line) => line.trim())
                .filter(Boolean),
            output_comparison: form.elements.output_comparison.value,
            timeout_seconds: Number(form.elements.timeout_seconds.value || 5),
            ignore_case: form.elements.ignore_case.checked,
            ignore_whitespace: form.elements.ignore_whitespace.checked,
            accept_alternative_solutions: form.elements.accept_alternative_solutions.checked,
            min_output_lines: Number(form.elements.min_output_lines.value || 0),
            required_patterns: collectRules(requiredRulesEl),
            forbidden_patterns: collectRules(forbiddenRulesEl),
            success_explanation: form.elements.success_explanation.value.trim(),
            failure_hint: form.elements.failure_hint.value.trim(),
            quiz: {
                enabled: quizToggle.checked,
                title: form.elements.quiz_title.value.trim(),
                instructions: form.elements.quiz_instructions.value.trim(),
                passing_score: Number(form.elements.quiz_passing_score.value || 70),
                max_attempts: Number(form.elements.quiz_max_attempts.value || 0),
                is_published: form.elements.quiz_is_published.checked,
                questions: collectQuestions(),
            },
        };
        const data = await request(`${API_BASE}/activities/${form.elements.lecture_id.value}/`, {
            method: "POST",
            body: JSON.stringify(payload),
        });
        populateForm(data.item);
        await loadActivityList();
        setFeedback(feedback, data.message, "success");
    });

    const lookupData = await loadLookups();
    fillSelect(filterCourse, lookupData.courses, { blankLabel: "All courses" });
    await loadActivityList();
    resetForm();
}

async function initProgressPage(root) {
    const summaryEl = root.querySelector("[data-progress-summary]");
    const rowsEl = root.querySelector("[data-progress-rows]");
    const filterCourse = root.querySelector("[data-progress-filter-course]");

    async function loadProgress() {
        const query = filterCourse.value ? `?course=${encodeURIComponent(filterCourse.value)}` : "";
        const data = await request(`${API_BASE}/progress/${query}`);
        fillSelect(filterCourse, data.courses, { blankLabel: "All courses" });
        if (query) {
            filterCourse.value = new URLSearchParams(query.slice(1)).get("course");
        }

        summaryEl.innerHTML = [
            createMetricCard("Enrollments", data.summary.total_enrollments, "Tracked in this view"),
            createMetricCard("Completed", data.summary.completed_enrollments, "Finished course journeys"),
            createMetricCard("Completion rate", `${data.summary.completion_rate}%`, "Across filtered enrollments"),
            createMetricCard("Active courses", data.summary.active_courses, "Represented in the table"),
        ].join("");

        if (!data.items.length) {
            rowsEl.innerHTML = `<tr><td colspan="7"><div class="admin-empty-state"><p>No learner progress matches this filter.</p></div></td></tr>`;
            return;
        }

        rowsEl.innerHTML = data.items
            .map(
                (item) => `
                    <tr>
                        <td><strong>${escapeHtml(item.user_name)}</strong><br><span>${escapeHtml(item.user_email)}</span></td>
                        <td>${escapeHtml(item.course_title)}</td>
                        <td>${createProgressBar(item.progress_percent)}</td>
                        <td>${escapeHtml(item.completed_lessons)}/${escapeHtml(item.total_lessons)}</td>
                        <td>${escapeHtml(item.completed_activities)}/${escapeHtml(item.total_activities)}</td>
                        <td>${escapeHtml(item.passed_quizzes)}/${escapeHtml(item.total_quizzes)}</td>
                        <td><span class="admin-status-pill ${item.status === "Completed" ? "" : "admin-status-pill--warn"}">${escapeHtml(item.status)}</span></td>
                    </tr>
                `
            )
            .join("");
    }

    filterCourse.addEventListener("change", loadProgress);
    await loadProgress();
}

async function initUsersPage(root) {
    const summaryEl = root.querySelector("[data-user-summary]");
    const listEl = root.querySelector("[data-user-list]");
    const form = root.querySelector("[data-user-form]");
    const feedback = root.querySelector("[data-user-feedback]");
    const titleEl = root.querySelector("[data-user-form-title]");
    const metaEl = root.querySelector("[data-user-meta]");
    const filterRole = root.querySelector("[data-user-filter-role]");
    let currentId = "";

    function renderSummary(summary) {
        summaryEl.innerHTML = [
            createMetricCard("Accounts", summary.total_accounts, "Registered users across the platform"),
            createMetricCard("Active", summary.active_accounts, "Accounts currently enabled"),
            createMetricCard("Admins", summary.admin_accounts, "System-management accounts"),
            createMetricCard("Learners", summary.learner_accounts, "Learner-only accounts"),
            createMetricCard("Online now", summary.online_accounts, "Seen within the last 5 minutes"),
        ].join("");
    }

    function resetForm() {
        currentId = "";
        form.reset();
        form.elements.user_id.value = "";
        form.elements.username_display.value = "";
        titleEl.textContent = "Select a user";
        metaEl.textContent = "Open an account from the list to manage role and status.";
        setFeedback(feedback, "");
        Array.from(listEl.querySelectorAll("[data-user-item]")).forEach((button) => button.classList.remove("is-active"));
    }

    function populateForm(item) {
        currentId = item.id;
        form.elements.user_id.value = item.id;
        form.elements.username_display.value = item.username || "";
        form.elements.role.value = item.role || "learner";
        form.elements.first_name.value = item.first_name || "";
        form.elements.last_name.value = item.last_name || "";
        form.elements.email.value = item.email || "";
        form.elements.is_active.checked = Boolean(item.is_active);
        titleEl.textContent = item.display_name || item.username;
        metaEl.textContent = [
            item.role_label,
            item.is_superuser ? "Superuser" : item.is_staff ? "Admin staff" : "Learner access",
            `${item.enrollment_count ?? 0} enrollments`,
            `${item.badge_count ?? 0} badges`,
            `${item.certificate_count ?? 0} certificates`,
        ].join(" / ");
        Array.from(listEl.querySelectorAll("[data-user-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.userItem === String(item.id));
        });
    }

    async function loadUsers(selectedId = currentId) {
        const query = filterRole.value ? `?role=${encodeURIComponent(filterRole.value)}` : "";
        const data = await request(`${API_BASE}/users/${query}`);
        renderSummary(data.summary);

        if (!data.items.length) {
            renderEmpty(listEl, "No accounts match the current role filter.");
            resetForm();
            return;
        }

        listEl.innerHTML = data.items
            .map(
                (item) => `
                    <button type="button" class="admin-list__item" data-user-item="${item.id}">
                        <span class="admin-list__title">${escapeHtml(item.display_name || item.username)}</span>
                        <span class="admin-list__meta">${escapeHtml(item.email || item.username)}</span>
                        <span class="admin-list__submeta">
                            <span>${escapeHtml(item.role_label)}</span>
                            <span>${item.is_active ? "Active" : "Inactive"}</span>
                            <span>${escapeHtml(item.enrollment_count ?? 0)} enrollments</span>
                        </span>
                    </button>
                `
            )
            .join("");

        if (selectedId && data.items.some((item) => String(item.id) === String(selectedId))) {
            currentId = selectedId;
            Array.from(listEl.querySelectorAll("[data-user-item]")).forEach((button) => {
                button.classList.toggle("is-active", button.dataset.userItem === String(currentId));
            });
        } else {
            resetForm();
        }
    }

    listEl.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-user-item]");
        if (!button) {
            return;
        }
        const data = await request(`${API_BASE}/users/${button.dataset.userItem}/`);
        populateForm(data.item);
    });

    filterRole.addEventListener("change", () => loadUsers());
    root.querySelector('[data-action="refresh-users"]').addEventListener("click", () => loadUsers());

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.elements.user_id.value) {
            setFeedback(feedback, "Select a user account before saving changes.", "error");
            return;
        }
        const data = await request(`${API_BASE}/users/${form.elements.user_id.value}/`, {
            method: "POST",
            body: JSON.stringify({
                first_name: form.elements.first_name.value.trim(),
                last_name: form.elements.last_name.value.trim(),
                email: form.elements.email.value.trim(),
                role: form.elements.role.value,
                is_active: form.elements.is_active.checked,
            }),
        });
        populateForm(data.item);
        await loadUsers(data.item.id);
        setFeedback(feedback, data.message, "success");
    });

    await loadUsers();
}

async function initBadgesPage(root) {
    const listEl = root.querySelector("[data-badge-list]");
    const form = root.querySelector("[data-badge-form]");
    const feedback = root.querySelector("[data-badge-feedback]");
    const titleEl = root.querySelector("[data-badge-form-title]");
    const deleteButton = root.querySelector('[data-action="delete-badge"]');
    const courseSelect = root.querySelector("[data-badge-course-select]");
    let currentId = "";

    async function loadCourses() {
        const data = await request(`${API_BASE}/courses/?compact=1`);
        fillSelect(courseSelect, data.items, { blankLabel: "Platform-wide" });
    }

    async function loadBadges(selectedId = currentId) {
        const data = await request(`${API_BASE}/badges/`);
        if (!data.items.length) {
            renderEmpty(listEl, "No badges yet. Create the first reward.");
            return;
        }
        listEl.innerHTML = data.items
            .map(
                (item) => `
                    <button type="button" class="admin-list__item" data-badge-item="${item.id}">
                        <span class="admin-list__title">${escapeHtml(item.name)}</span>
                        <span class="admin-list__meta">${escapeHtml(item.course_title)} / ${escapeHtml(item.award_type_label)}</span>
                        <span class="admin-list__submeta">
                            <span>${escapeHtml(item.xp_reward)} XP</span>
                            <span>${escapeHtml(item.award_count ?? 0)} awards</span>
                        </span>
                    </button>
                `
            )
            .join("");
        currentId = selectedId;
        Array.from(listEl.querySelectorAll("[data-badge-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.badgeItem === String(currentId));
        });
    }

    function resetForm() {
        currentId = "";
        form.reset();
        form.elements.badge_id.value = "";
        form.elements.xp_reward.value = 40;
        form.elements.is_active.checked = true;
        titleEl.textContent = "New badge";
        deleteButton.hidden = true;
        setFeedback(feedback, "");
        Array.from(listEl.querySelectorAll("[data-badge-item]")).forEach((button) => button.classList.remove("is-active"));
    }

    function populateForm(item) {
        currentId = item.id;
        form.elements.badge_id.value = item.id;
        form.elements.name.value = item.name || "";
        form.elements.description.value = item.description || "";
        form.elements.course.value = item.course_id || "";
        form.elements.award_type.value = item.award_type || "milestone";
        form.elements.criteria_key.value = item.criteria_key || "";
        form.elements.xp_reward.value = item.xp_reward || 40;
        form.elements.is_active.checked = Boolean(item.is_active);
        titleEl.textContent = item.name;
        deleteButton.hidden = false;
        Array.from(listEl.querySelectorAll("[data-badge-item]")).forEach((button) => {
            button.classList.toggle("is-active", button.dataset.badgeItem === String(item.id));
        });
    }

    listEl.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-badge-item]");
        if (!button) {
            return;
        }
        const data = await request(`${API_BASE}/badges/${button.dataset.badgeItem}/`);
        populateForm(data.item);
    });

    root.querySelector('[data-action="new-badge"]').addEventListener("click", resetForm);
    root.querySelector('[data-action="reset-badge"]').addEventListener("click", resetForm);
    root.querySelector('[data-action="refresh-badges"]').addEventListener("click", () => loadBadges());

    deleteButton.addEventListener("click", async () => {
        if (!currentId || !window.confirm("Delete this badge?")) {
            return;
        }
        await request(`${API_BASE}/badges/${currentId}/`, { method: "DELETE" });
        resetForm();
        await loadBadges();
        setFeedback(feedback, "Badge deleted successfully.", "success");
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const id = form.elements.badge_id.value;
        const endpoint = id ? `${API_BASE}/badges/${id}/` : `${API_BASE}/badges/`;
        const data = await request(endpoint, { method: "POST", body: new FormData(form) });
        populateForm(data.item);
        await loadBadges(data.item.id);
        setFeedback(feedback, data.message, "success");
    });

    await loadCourses();
    await loadBadges();
    resetForm();
}

async function initCertificatesPage(root) {
    const summaryEl = root.querySelector("[data-certificate-summary]");
    const listEl = root.querySelector("[data-certificate-list]");
    const pendingEl = root.querySelector("[data-pending-certificates]");

    async function loadCertificates() {
        const data = await request(`${API_BASE}/certificates/`);
        summaryEl.innerHTML = [
            createMetricCard("Issued", data.summary.issued_count, "Certificate files generated"),
            createMetricCard("Pending", data.summary.pending_count, "Completed courses without a certificate"),
        ].join("");

        if (!data.items.length) {
            renderEmpty(listEl, "No certificates have been issued yet.");
        } else {
            listEl.innerHTML = data.items
                .map(
                    (item) => `
                        <article class="admin-certificate-card">
                            <span class="admin-mini-card__label">${escapeHtml(item.course_title)}</span>
                            <strong>${escapeHtml(item.user_name)}</strong>
                            <p>${escapeHtml(item.user_email || "No email address")}</p>
                            <p>Issued ${escapeHtml(item.issued_at ? formatDate(item.issued_at) : "Pending file date")}</p>
                            <div class="admin-certificate-card__actions">
                                ${
                                    item.file_url
                                        ? `<a href="${escapeHtml(item.file_url)}" target="_blank" rel="noopener noreferrer">Open file</a>`
                                        : ""
                                }
                                <button type="button" class="admin-button admin-button--ghost" data-action="refresh-certificate" data-certificate-id="${item.id}">Refresh</button>
                                <button type="button" class="admin-button admin-button--ghost" data-action="email-certificate" data-certificate-id="${item.id}">Email</button>
                            </div>
                        </article>
                    `
                )
                .join("");
        }

        if (!data.pending.length) {
            pendingEl.innerHTML = `<tr><td colspan="4"><div class="admin-empty-state"><p>All eligible completions already have certificates.</p></div></td></tr>`;
        } else {
            pendingEl.innerHTML = data.pending
                .map(
                    (item) => `
                        <tr>
                            <td><strong>${escapeHtml(item.user_name)}</strong><br><span>${escapeHtml(item.user_email)}</span></td>
                            <td>${escapeHtml(item.course_title)}</td>
                            <td>${escapeHtml(formatDate(item.completed_at))}</td>
                            <td><button type="button" class="admin-button admin-button--ghost" data-action="issue-certificate" data-user-id="${item.user_id}" data-course-id="${item.course_id}">Issue</button></td>
                        </tr>
                    `
                )
                .join("");
        }
    }

    root.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-action]");
        if (!button) {
            return;
        }
        if (button.dataset.action === "refresh-certificate") {
            await request(`${API_BASE}/certificates/${button.dataset.certificateId}/refresh/`, { method: "POST" });
            await loadCertificates();
        }
        if (button.dataset.action === "email-certificate") {
            await request(`${API_BASE}/certificates/${button.dataset.certificateId}/email/`, { method: "POST" });
            await loadCertificates();
        }
        if (button.dataset.action === "issue-certificate") {
            await request(`${API_BASE}/certificates/issue/`, {
                method: "POST",
                body: JSON.stringify({
                    user_id: Number(button.dataset.userId),
                    course_id: Number(button.dataset.courseId),
                }),
            });
            await loadCertificates();
        }
    });

    await loadCertificates();
}

document.addEventListener("DOMContentLoaded", async () => {
    const root = document.querySelector("[data-admin-screen]");
    if (!root) {
        return;
    }

    try {
        switch (root.dataset.adminScreen) {
            case "dashboard":
                await initDashboardPage(root);
                break;
            case "courses":
                await initCoursesPage(root);
                break;
            case "lectures":
                await initLecturesPage(root);
                break;
            case "materials":
                await initMaterialsPage(root);
                break;
            case "activities":
                await initActivitiesPage(root);
                break;
            case "progress":
                await initProgressPage(root);
                break;
            case "users":
                await initUsersPage(root);
                break;
            case "badges":
                await initBadgesPage(root);
                break;
            case "certificates":
                await initCertificatesPage(root);
                break;
            default:
                break;
        }
    } catch (error) {
        window.console.error(error);
        const fallback = root.querySelector(".admin-feedback");
        if (fallback) {
            setFeedback(fallback, error.message || "Unable to load this admin section.", "error");
        } else {
            root.insertAdjacentHTML(
                "afterbegin",
                `<div class="admin-message admin-message--error">${escapeHtml(error.message || "Unable to load this admin section.")}</div>`
            );
        }
    }
});
