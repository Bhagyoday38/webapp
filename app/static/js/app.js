const input = document.getElementById("files");
const list = document.getElementById("file-list");
const dropzone = document.getElementById("dropzone");

function renderFiles() {

    if (!input || !list) {
        return;
    }

    list.innerHTML = "";

    Array.from(input.files).forEach((file, index) => {

        const row = document.createElement("div");

        row.className = "card";

        row.innerHTML =
            `<strong>${index + 1}. ${file.name}</strong>
             <span class="muted">
                 ${(file.size / 1024 / 1024).toFixed(2)} MB
             </span>`;

        list.appendChild(row);
    });
}

if (input) {
    input.addEventListener("change", renderFiles);
}

if (dropzone && input) {

    dropzone.addEventListener("dragover", function(event) {
        event.preventDefault();
        dropzone.style.borderColor = "#2563eb";
    });

    dropzone.addEventListener("dragleave", function() {
        dropzone.style.borderColor = "#9ca3af";
    });

    dropzone.addEventListener("drop", function(event) {

        event.preventDefault();

        input.files = event.dataTransfer.files;

        renderFiles();

        dropzone.style.borderColor = "#9ca3af";
    });
}
