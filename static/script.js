// Clearance Face Search - Frontend JavaScript

class ClearanceFaceSearch {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.setupDragAndDrop();
    }

    initializeElements() {
        this.form = document.getElementById('searchForm');
        this.uploadArea = document.getElementById('uploadArea');
        this.faceFile = document.getElementById('faceFile');
        this.imagePreview = document.getElementById('imagePreview');
        this.previewImg = document.getElementById('previewImg');
        this.removeImage = document.getElementById('removeImage');
        this.thresholdSlider = document.getElementById('faceThreshold');
        this.thresholdValue = document.getElementById('thresholdValue');
        this.searchBtn = document.getElementById('searchBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.resultsInfo = document.getElementById('resultsInfo');
        this.resultsContent = document.getElementById('resultsContent');
        this.loadingContainer = document.getElementById('loadingContainer');
        
        this.selectedImage = null;
    }

    bindEvents() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Clear form
        this.clearBtn.addEventListener('click', () => this.clearForm());
        
        // File upload
        this.uploadArea.addEventListener('click', () => this.faceFile.click());
        this.faceFile.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Remove image
        this.removeImage.addEventListener('click', () => this.removeSelectedImage());
        
        // Threshold slider
        this.thresholdSlider.addEventListener('input', (e) => {
            this.thresholdValue.textContent = e.target.value;
        });
    }

    setupDragAndDrop() {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        this.uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    handleFile(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            this.showMessage('Hanya file gambar yang diperbolehkan', 'error');
            return;
        }

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            this.showMessage('Ukuran file maksimal 5MB', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.selectedImage = e.target.result;
            this.previewImg.src = this.selectedImage;
            this.uploadArea.style.display = 'none';
            this.imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    removeSelectedImage() {
        this.selectedImage = null;
        this.faceFile.value = '';
        this.uploadArea.style.display = 'block';
        this.imagePreview.style.display = 'none';
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        // Validate form
        if (!this.validateForm()) {
            return;
        }

        this.showLoading(true);
        this.hideResults();

        try {
            const formData = this.getFormData();
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Terjadi kesalahan pada server');
            }

            this.displayResults(result);

        } catch (error) {
            this.showMessage(`Error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    validateForm() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const name = document.getElementById('name').value.trim();
        const nik = document.getElementById('nik').value.trim();

        if (!username || !password) {
            this.showMessage('Username dan password harus diisi', 'error');
            return false;
        }

        if (!name && !nik) {
            this.showMessage('Minimal isi nama atau NIK untuk membatasi hasil', 'error');
            return false;
        }

        return true;
    }

    getFormData() {
        const formData = {
            username: document.getElementById('username').value.trim(),
            password: document.getElementById('password').value.trim(),
            name: document.getElementById('name').value.trim(),
            nik: document.getElementById('nik').value.trim(),
            page: document.getElementById('page').value,
            face_threshold: parseFloat(this.thresholdSlider.value),
            save_face: document.getElementById('saveFace').checked
        };

        if (this.selectedImage) {
            formData.face_query = this.selectedImage;
        }

        return formData;
    }

    displayResults(result) {
        this.resultsInfo.textContent = result.message || 'Hasil pencarian';
        this.resultsContent.innerHTML = '';

        if (!result.results || result.results.length === 0) {
            this.resultsContent.innerHTML = `
                <div class="message info">
                    <i class="fas fa-info-circle"></i>
                    Tidak ada hasil yang ditemukan
                </div>
            `;
        } else {
            result.results.forEach((item, index) => {
                const resultElement = this.createResultElement(item, index + 1);
                this.resultsContent.appendChild(resultElement);
            });
        }

        this.resultsContainer.style.display = 'block';
        this.resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    createResultElement(item, index) {
        const div = document.createElement('div');
        div.className = 'result-item';

        const person = item.person || item;
        const distance = item.distance;
        const savedPath = item.saved_face_path;

        let faceHtml = '';
        if (person.face) {
            faceHtml = `
                <div class="result-face">
                    <img src="data:image/jpeg;base64,${person.face}" alt="Face">
                    ${savedPath ? `<p><small>Disimpan: ${savedPath}</small></p>` : ''}
                </div>
            `;
        }

        div.innerHTML = `
            <div class="result-header">
                <div class="result-title">${person.full_name || 'Nama tidak tersedia'}</div>
                ${distance !== undefined ? `<div class="result-score">Score: ${distance.toFixed(3)}</div>` : ''}
            </div>
            <div class="result-details">
                <div class="detail-item">
                    <div class="detail-label">NIK</div>
                    <div class="detail-value">${person.ktp_number || 'Tidak tersedia'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Tanggal Lahir</div>
                    <div class="detail-value">${person.date_of_birth || 'Tidak tersedia'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Tempat Lahir</div>
                    <div class="detail-value">${person.birth_place || 'Tidak tersedia'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Alamat</div>
                    <div class="detail-value">${person.address || 'Tidak tersedia'}</div>
                </div>
            </div>
            ${faceHtml}
        `;

        return div;
    }

    showLoading(show) {
        this.loadingContainer.style.display = show ? 'block' : 'none';
        this.searchBtn.disabled = show;
        this.searchBtn.innerHTML = show ? 
            '<i class="fas fa-spinner fa-spin"></i> Memproses...' : 
            '<i class="fas fa-search"></i> Mulai Pencarian';
    }

    hideResults() {
        this.resultsContainer.style.display = 'none';
    }

    clearForm() {
        this.form.reset();
        this.removeSelectedImage();
        this.hideResults();
        this.thresholdValue.textContent = '0.50';
        this.searchBtn.disabled = false;
        this.searchBtn.innerHTML = '<i class="fas fa-search"></i> Mulai Pencarian';
    }

    showMessage(message, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());

        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            ${message}
        `;

        // Insert after form
        this.form.parentNode.insertBefore(messageDiv, this.form.nextSibling);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ClearanceFaceSearch();
});

// Health check on page load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/health');
        const health = await response.json();
        
        if (!health.face_lib_available) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message error';
            messageDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                Warning: Face recognition library tidak tersedia. Fitur face search tidak akan berfungsi.
            `;
            document.querySelector('.main-content').insertBefore(messageDiv, document.querySelector('.search-form-container'));
        }
    } catch (error) {
        console.warn('Health check failed:', error);
    }
});
