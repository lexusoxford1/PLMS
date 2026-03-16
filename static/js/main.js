document.addEventListener("DOMContentLoaded", () => {
    const messages = document.querySelectorAll(".message");
    messages.forEach((message) => {
        setTimeout(() => {
            message.style.opacity = "0.96";
        }, 200);
    });
});
