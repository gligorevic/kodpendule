"use strict";
document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("xml-dropzone");
    const fileInput = document.getElementById("id_xml_file");
    const filename = document.getElementById("xml-file-name");
    if (dropzone && fileInput) {
        const showFile = () => { filename.textContent = fileInput.files[0]?.name || ""; };
        fileInput.addEventListener("change", showFile);
        ["dragenter", "dragover"].forEach(name => dropzone.addEventListener(name, event => {
            event.preventDefault();
            dropzone.classList.add("is-dragging");
        }));
        ["dragleave", "drop"].forEach(name => dropzone.addEventListener(name, event => {
            event.preventDefault();
            dropzone.classList.remove("is-dragging");
        }));
        dropzone.addEventListener("drop", event => {
            if (event.dataTransfer.files.length !== 1) return;
            fileInput.files = event.dataTransfer.files;
            showFile();
        });
    }
    let categoriesChanged = false;
    document.querySelectorAll("select[name^='category_']").forEach(select => {
        select.addEventListener("change", () => {
            categoriesChanged = true;
            const apply = document.querySelector("#xml-apply-form button");
            if (apply) apply.disabled = true;
        });
    });
    document.querySelectorAll("form").forEach(form => {
        form.addEventListener("submit", () => { categoriesChanged = false; });
    });
    window.addEventListener("beforeunload", event => {
        if (categoriesChanged) { event.preventDefault(); event.returnValue = ""; }
    });
});
