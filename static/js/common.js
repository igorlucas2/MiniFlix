const ready = (fn) => {
    if (document.readyState !== "loading") {
        fn();
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
};

ready(() => {
    const images = document.querySelectorAll("img");

    const markLoaded = (img) => {
        img.classList.add("loaded");
        const wrapper = img.closest(".skeleton");
        if (wrapper) {
            wrapper.classList.add("loaded");
        }
    };

    images.forEach((img) => {
        if (img.complete) {
            markLoaded(img);
        } else {
            img.addEventListener("load", () => markLoaded(img));
        }
    });
});
