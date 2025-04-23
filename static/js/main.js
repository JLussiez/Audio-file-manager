document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadToast = new bootstrap.Toast(document.getElementById('uploadToast'));

    // Gestionnaire d'événements pour la zone de dépôt
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#666';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#ccc';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#ccc';
        handleFiles(e.dataTransfer.files);
    });

    // Gestionnaire d'événements pour la sélection de fichiers
    fileInput.addEventListener('change', () => handleFiles(fileInput.files));

    // Gestionnaire d'événements pour les boutons de suppression
    document.querySelectorAll('.delete-file').forEach(button => {
        button.addEventListener('click', function() {
            const filename = this.dataset.filename;
            if (confirm('Êtes-vous sûr de vouloir supprimer ce fichier ?')) {
                deleteFile(filename);
            }
        });
    });
});

function formatSize(bytes) {
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function showToast(message) {
    document.getElementById('toastBody').textContent = message;
    uploadToast.show();
}

function handleFiles(files) {
    for (let file of files) {
        if (file.size > 20 * 1024 * 1024) {
            showToast('Le fichier ' + file.name + ' dépasse la taille maximale de 20MB');
            continue;
        }
        uploadFile(file);
    }
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error);
        } else {
            let message = 'Fichier téléchargé avec succès';
            if (data.compression_info) {
                message += `\nCompression: ${data.compression_info.compression_ratio}% d'économie`;
                message += `\nTaille originale: ${formatSize(data.compression_info.original_size)}`;
                message += `\nTaille compressée: ${formatSize(data.compression_info.compressed_size)}`;
            }
            showToast(message);
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Une erreur est survenue lors du téléchargement');
    });
}

function deleteFile(filename) {
    fetch(`/delete/${filename}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast(data.error);
        } else {
            showToast('Fichier supprimé avec succès');
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Une erreur est survenue lors de la suppression');
    });
} 