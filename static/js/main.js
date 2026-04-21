const toggleBtn = document.getElementById("themeToggle");

const currentTheme = localStorage.getItem("theme");

if (currentTheme) {
    document.body.setAttribute("data-theme", currentTheme);
    toggleBtn.textContent = currentTheme === "dark" ? "🌙" : "☀";
}

toggleBtn.addEventListener("click", () => {
    let theme = document.body.getAttribute("data-theme");

    if (theme === "dark") {
        document.body.setAttribute("data-theme", "light");
        localStorage.setItem("theme", "light");
        toggleBtn.textContent = "☀";
    } else {
        document.body.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
        toggleBtn.textContent = "🌙";
    }
});

document.addEventListener('DOMContentLoaded', function() {
    
    function setupDropZone(dropZoneId, fileInputId, previewContainerId) {
        const dropZone = document.getElementById(dropZoneId);
        const fileInput = document.getElementById(fileInputId);
        const previewContainer = document.getElementById(previewContainerId);
        
        if (!dropZone || !fileInput || !previewContainer) return;

        let dataTransfer = new DataTransfer();

        dropZone.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.background = 'rgba(79, 70, 229, 0.1)';
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.style.background = 'var(--surface-2)';
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            handleFiles(files);
        });

        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });

        function handleFiles(files) {
            Array.from(files).forEach(file => {
                if (!file.type.match('image.*')) return;
                
                dataTransfer.items.add(file);
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewDiv = document.createElement('div');
                    previewDiv.className = 'position-relative rounded-3 overflow-hidden shadow-sm';
                    previewDiv.style.width = '100px';
                    previewDiv.style.height = '100px';
                    
                    previewDiv.innerHTML = `
                        <img src="${e.target.result}" class="w-100 h-100" style="object-fit: cover;" alt="Preview">
                        <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1 p-0 rounded-circle d-flex align-items-center justify-content-center delete-btn" style="width: 20px; height: 20px;" data-name="${file.name}">
                            <i class="bi bi-x" style="font-size: 12px;"></i>
                        </button>
                    `;
                    
                    previewContainer.appendChild(previewDiv);

                    previewDiv.querySelector('.delete-btn').addEventListener('click', function(e) {
                        e.stopPropagation();
                        const fileName = this.getAttribute('data-name');
                        
                        const newDataTransfer = new DataTransfer();
                        Array.from(dataTransfer.files).forEach(f => {
                            if (f.name !== fileName) newDataTransfer.items.add(f);
                        });
                        
                        dataTransfer.items.clear();
                        Array.from(newDataTransfer.files).forEach(f => dataTransfer.items.add(f));

                        fileInput.files = dataTransfer.files;
                        previewDiv.remove();
                    });
                }
                reader.readAsDataURL(file);
            });
            
            fileInput.files = dataTransfer.files;
        }
    }

    setupDropZone('blog-drop-zone', 'blog-file-input', 'blog-preview-container');

});

    if (typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: 'textarea[name="content"]', 
            plugins: 'lists link code wordcount',
            toolbar: 'undo redo | formatselect | bold italic | alignleft aligncenter alignright | bullist numlist | link code',
            menubar: false,
            height: 400,
            border_radius: '12px',
            skin: document.body.getAttribute('data-theme') === 'dark' ? 'oxide-dark' : 'oxide',
            content_css: document.body.getAttribute('data-theme') === 'dark' ? 'dark' : 'default',
            setup: function (editor) {
                editor.on('change', function () {
                    tinymce.triggerSave(); 
                });
            }
        });
    }

const filterBtns = document.querySelectorAll('.filter-btn');
    const projectWrappers = document.querySelectorAll('.project-wrapper');

    if (filterBtns.length > 0 && projectWrappers.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                
                filterBtns.forEach(b => {
                    b.classList.remove('btn-primary', 'active');
                    b.classList.add('btn-outline-primary');
                });
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-primary', 'active');

                const filterValue = btn.getAttribute('data-filter');

                projectWrappers.forEach(wrapper => {
                    const tags = wrapper.getAttribute('data-tags');
                    
                    if (filterValue === 'all' || tags.includes(filterValue)) {
                        wrapper.style.display = 'block';

                        wrapper.animate([
                            { opacity: 0, transform: 'translateY(10px)' }, 
                            { opacity: 1, transform: 'translateY(0)' }
                        ], { duration: 300, fill: 'forwards' });
                    } else {
                        wrapper.style.display = 'none';
                    }
                });
            });
        });
    }

const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault(); 
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnHtml = submitBtn.innerHTML;
            const alertContainer = document.getElementById('form-alert-container');
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Sending...';
            
            try {
                const formData = new FormData(this);
                const response = await fetch('/contact', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest' 
                    }
                });

                const result = await response.json();

                if (result.status === 'success') {
                    alertContainer.innerHTML = `
                        <div class="alert alert-success alert-dismissible fade show shadow-sm rounded-4 border-0 d-flex align-items-center mb-4" style="animation: slideDown 0.3s ease-out;">
                            <i class="bi bi-check-circle-fill me-3 fs-5"></i>
                            <div>${result.message}</div>
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    `;
                    contactForm.reset();
                }
            } catch (error) {
                console.error('Error sending message:', error);
                alertContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show shadow-sm rounded-4 border-0 d-flex align-items-center mb-4">
                        <i class="bi bi-exclamation-triangle-fill me-3 fs-5"></i>
                        <div>Something went wrong. Please try again later.</div>
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHtml;
            }
        });
    }