// Handle copy to clipboard functionality
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        // Show toast notification
        const toast = document.getElementById('copyToast');
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Auto-resize textarea
    const textareas = document.querySelectorAll('.auto-resize-textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            
            // Update character count
            const counter = document.getElementById('textCounter');
            if (counter) {
                counter.textContent = `${this.value.length} characters`;
            }
        });
    });
    
    // Handle paste from clipboard for URL
    const pasteUrlBtn = document.getElementById('paste-url');
    if (pasteUrlBtn) {
        pasteUrlBtn.addEventListener('click', function() {
            navigator.clipboard.readText().then(text => {
                document.getElementById('url').value = text.trim();
            }).catch(err => {
                console.error('Failed to read clipboard: ', err);
            });
        });
    }
    
    // Handle paste from clipboard for text
    const pasteTextBtn = document.getElementById('paste-text');
    if (pasteTextBtn) {
        pasteTextBtn.addEventListener('click', function() {
            navigator.clipboard.readText().then(text => {
                const textarea = document.getElementById('text');
                textarea.value = text;
                textarea.dispatchEvent(new Event('input'));
            }).catch(err => {
                console.error('Failed to read clipboard: ', err);
            });
        });
    }
    
    // Handle range slider value display
    const maxLengthSlider = document.getElementById('max_length');
    const lengthValue = document.getElementById('lengthValue');
    if (maxLengthSlider && lengthValue) {
        maxLengthSlider.addEventListener('input', function() {
            lengthValue.textContent = `${this.value} words`;
        });
    }
    
    const maxLengthSlider2 = document.getElementById('max_length2');
    const lengthValue2 = document.getElementById('lengthValue2');
    if (maxLengthSlider2 && lengthValue2) {
        maxLengthSlider2.addEventListener('input', function() {
            lengthValue2.textContent = `${this.value} words`;
        });
    }
    
    // Handle form submissions with loading overlay
    const urlForm = document.getElementById('urlForm');
    const textForm = document.getElementById('textForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (urlForm) {
        urlForm.addEventListener('submit', function() {
            if (this.checkValidity()) {
                loadingOverlay.classList.add('show');
            }
        });
    }
    
    if (textForm) {
        textForm.addEventListener('submit', function() {
            if (this.checkValidity()) {
                loadingOverlay.classList.add('show');
            }
        });
    }
    
    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-moon')) {
                icon.classList.replace('fa-moon', 'fa-sun');
            } else {
                icon.classList.replace('fa-sun', 'fa-moon');
            }
            
            // Save preference to localStorage
            const isDarkMode = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);
        });
        
        // Check for saved preference
        const savedDarkMode = localStorage.getItem('darkMode') === 'true';
        if (savedDarkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.querySelector('i').classList.replace('fa-moon', 'fa-sun');
        }
    }
    
    // Load news articles on page load
    loadNews();
    
    // Refresh news on button click
    const refreshNewsBtn = document.getElementById('refreshNews');
    if (refreshNewsBtn) {
        refreshNewsBtn.addEventListener('click', function() {
            loadNews();
        });
    }
    
    // Handle news category change
    const newsCategory = document.getElementById('newsCategory');
    if (newsCategory) {
        newsCategory.addEventListener('change', function() {
            loadNews();
        });
    }
});

// Function to load news articles
function loadNews() {
    const newsContainer = document.getElementById('newsContainer');
    const category = document.getElementById('newsCategory').value;
    
    if (newsContainer) {
        newsContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading news articles...</p>
            </div>
        `;
        
        fetch(`/get_news?category=${category}`)
            .then(response => response.json())
            .then(data => {
                if (data.articles && data.articles.length > 0) {
                    let html = '';
                    data.articles.forEach(article => {
                        html += `
                            <div class="col-md-6 col-lg-4 mb-4">
                                <div class="card news-card">
                                    <img src="${article.image || '/static/img/news-placeholder.jpg'}" class="news-image card-img-top" alt="${article.title}" onerror="this.src='/static/img/news-placeholder.jpg'">
                                    <div class="card-body d-flex flex-column">
                                        <h6 class="card-title">${article.title}</h6>
                                        <p class="card-text small text-muted">${article.description || 'No description available.'}</p>
                                        <div class="mt-auto d-flex justify-content-between align-items-center">
                                            <small class="text-muted">${article.source}</small>
                                            <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-primary">Read</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    newsContainer.innerHTML = html;
                } else {
                    newsContainer.innerHTML = `
                        <div class="col-12 text-center py-5">
                            <i class="fas fa-newspaper mb-3" style="font-size: 3rem; color: #ccc;"></i>
                            <h6 class="text-muted">No news articles found</h6>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading news:', error);
                newsContainer.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-exclamation-circle mb-3" style="font-size: 3rem; color: #dc3545;"></i>
                        <h6 class="text-danger">Failed to load news</h6>
                        <p class="small text-muted">Please try again later</p>
                    </div>
                `;
            });
    }
}