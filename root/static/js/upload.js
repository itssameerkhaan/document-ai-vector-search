let files = [];
let recentlyUploadedFiles = [];
let countdownInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    // Drag and drop handlers
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
    
    // File input handler
    fileInput.addEventListener('change', handleFileSelect);
});

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('uploadZone').classList.add('dragging');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('uploadZone').classList.remove('dragging');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('uploadZone').classList.remove('dragging');
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
}

function handleFileSelect(e) {
    const selectedFiles = Array.from(e.target.files);
    addFiles(selectedFiles);
    e.target.value = ''; // Reset input
}

function addFiles(newFiles) {
    newFiles.forEach(file => {
        const fileData = {
            id: Math.random().toString(36).substr(2, 9),
            file: file,
            name: file.name,
            size: file.size,
            type: file.type,
            status: 'pending',
            progress: 0
        };
        files.push(fileData);
    });
    
    renderFiles();
}

function getFileIcon(filename, type) {
    const ext = filename.split('.').pop().toLowerCase();
    
    if (ext === 'pdf') return '<i class="fas fa-file-pdf file-icon pdf"></i>';
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)) 
        return '<i class="fas fa-file-image file-icon image"></i>';
    if (['xls', 'xlsx'].includes(ext)) 
        return '<i class="fas fa-file-excel file-icon excel"></i>';
    if (ext === 'csv') 
        return '<i class="fas fa-file-csv file-icon csv"></i>';
    if (['doc', 'docx'].includes(ext)) 
        return '<i class="fas fa-file-word file-icon word"></i>';
    return '<i class="fas fa-file file-icon default"></i>';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function renderFiles() {
    const container = document.getElementById('filesContainer');
    const filesList = document.getElementById('filesList');
    const fileCount = document.getElementById('fileCount');
    
    if (files.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    fileCount.textContent = files.length;
    
    filesList.innerHTML = files.map(fileData => {
        let statusHtml = '';
        
        if (fileData.status === 'pending') {
            statusHtml = '<i class="fas fa-clock status-icon pending"></i>';
        } else if (fileData.status === 'uploading') {
            statusHtml = `
                <i class="fas fa-spinner status-icon uploading spinning"></i>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${fileData.progress}%"></div>
                </div>
            `;
        } else if (fileData.status === 'success') {
            statusHtml = '<i class="fas fa-check-circle status-icon success"></i>';
        } else if (fileData.status === 'error') {
            statusHtml = '<i class="fas fa-exclamation-circle status-icon error"></i>';
        }
        
        return `
            <div class="file-item">
                ${getFileIcon(fileData.name, fileData.type)}
                <div class="file-info">
                    <div class="file-name">${fileData.name}</div>
                    <div class="file-size">${formatFileSize(fileData.size)}</div>
                </div>
                <div class="file-status">
                    ${statusHtml}
                </div>
                <div class="file-actions">
                    <button onclick="removeFile('${fileData.id}')" class="delete">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function removeFile(id) {
    files = files.filter(f => f.id !== id);
    renderFiles();
}

function clearAll() {
    files = [];
    renderFiles();
}

async function uploadFile(fileData) {
    const formData = new FormData();
    formData.append('file', fileData.file);
    
    try {
        fileData.status = 'uploading';
        renderFiles();
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            fileData.status = 'success';
            fileData.progress = 100;
            
            // Add to recently uploaded
            addToRecentlyUploaded({
                name: result.filename,
                size: result.size,
                uploadedAt: new Date().toLocaleString()
            });
            
            setTimeout(() => {
                files = files.filter(f => f.id !== fileData.id);
                renderFiles();
            }, 1500);
        } else {
            const error = await response.json();
            fileData.status = 'error';
            alert('Upload failed: ' + error.error);
        }
    } catch (error) {
        fileData.status = 'error';
        alert('Upload failed: ' + error.message);
    }
    
    renderFiles();
}

// Upload all files and keep loader until backend workflow finishes
function uploadAll() {
    const overlay = document.getElementById("loaderOverlay");
    overlay.classList.remove("hidden"); // show loader

    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) {
        alert("No pending files to upload.");
        overlay.classList.add("hidden");
        return;
    }

    let completed = 0;

    pendingFiles.forEach(async (fileData) => {
        await uploadFile(fileData);
        completed++;

        if (completed === pendingFiles.length) {
            console.log("All uploads done. Waiting for workflow...");
            pollWorkflowStatus(overlay);
        }
    });
}

// Poll Flask every 2s until workflow is done
function pollWorkflowStatus(overlay) {
    fetch("/workflow_status")
        .then(res => res.json())
        .then(data => {
            if (data.running) {
                console.log("Workflow still running...");
                setTimeout(() => pollWorkflowStatus(overlay), 2000);
            } else {
                console.log("🎉 Workflow completed!");
                overlay.classList.add("hidden"); // hide loader
                alert("All uploads and background processing completed!");
            }
        })
        .catch(err => {
            console.error("Error checking workflow status:", err);
            overlay.classList.add("hidden");
        });
}



function addToRecentlyUploaded(file) {
    recentlyUploadedFiles.push(file);
    renderRecentlyUploaded();
    startCountdown();
}

function renderRecentlyUploaded() {
    const container = document.getElementById('recentlyUploadedContainer');
    const list = document.getElementById('recentlyUploadedList');
    
    if (recentlyUploadedFiles.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    container.classList.remove('fade-out');
    
    list.innerHTML = recentlyUploadedFiles.map(file => `
        <div class="file-item">
            ${getFileIcon(file.name)}
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)} • ${file.uploadedAt}</div>
            </div>
            <div class="file-status">
                <i class="fas fa-check-circle status-icon success"></i>
            </div>
        </div>
    `).join('');
}

function startCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    
    let timeLeft = 10;
    const countdownElement = document.getElementById('countdown');
    countdownElement.textContent = timeLeft;
    
    countdownInterval = setInterval(() => {
        timeLeft--;
        countdownElement.textContent = timeLeft;
        if (timeLeft <= 0) {
            clearInterval(countdownInterval);
            hideRecentlyUploaded();
        }
    }, 1000);
}

function hideRecentlyUploaded() {
    const container = document.getElementById('recentlyUploadedContainer');
    container.classList.add('fade-out');
    
    setTimeout(() => {
        recentlyUploadedFiles = [];
        renderRecentlyUploaded();
    }, 500);
}
