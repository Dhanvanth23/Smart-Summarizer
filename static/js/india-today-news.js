// Static/js/india-today-news.js

document.addEventListener('DOMContentLoaded', function() {
    const newsContainer = document.getElementById('newsContainer');
    const refreshNewsBtn = document.getElementById('refreshNews');
    const newsCategorySelect = document.getElementById('newsCategory');
    
    // Function to fetch news
 // Update fetch function in india-today-news.js
async function fetchNews(category = null) {
    try {
        // Show loading state
        newsContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">Loading news articles...</p>
            </div>
        `;
        
        // Make API request without category parameter
        const response = await fetch(`/news/get_articles?count=20&language=en`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.articles && data.articles.length > 0) {
            displayNews(data.articles);
        } else {
            throw new Error('No articles found');
        }
    } catch (error) {
        console.error('Error fetching news:', error);
        displayError('Unable to load news at this time. Please try again later.');
    }
}
    
    // Function to display news articles
    function displayNews(articles) {
        // Clear the container
        newsContainer.innerHTML = '';
        
        // Create a row for articles
        const newsRow = document.createElement('div');
        newsRow.className = 'row';
        
        // Process each article
        articles.forEach(article => {
            // Create card for article
            const articleCard = document.createElement('div');
            articleCard.className = 'col-md-3 mb-4';
            
            // Ensure image URL is valid
            const imageUrl = article.image && article.image !== '' ? 
                article.image : '/static/img/news-placeholder.jpg';
            
            // Format description
            const description = article.description && article.description.length > 120 ? 
                article.description.substring(0, 120) + '...' : 
                article.description || 'No description available';
                
            // Format date if available
            let publishedDate = '';
            if (article.published_at) {
                try {
                    const date = new Date(article.published_at);
                    publishedDate = date.toLocaleDateString();
                } catch (e) {
                    publishedDate = article.published_at;
                }
            }
            
            // Create card HTML
            articleCard.innerHTML = `
                <div class="card h-100 news-card">
                    <div class="card-img-container">
                        <img src="${imageUrl}" class="card-img-top" alt="${article.title}" onerror="this.src='/static/img/news-placeholder.jpg'">
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">${article.title}</h6>
                        <p class="card-text small text-muted">${description}</p>
                    </div>
                    <div class="card-footer bg-transparent d-flex justify-content-between align-items-center">
                        <small class="text-muted">${article.source || 'India Today'}</small>
                        <small class="text-muted">${publishedDate}</small>
                    </div>
                    <div class="card-action">
                        <div class="d-flex justify-content-between">
                            <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-primary">Read More</a>
                            <button class="btn btn-sm btn-outline-secondary summarize-btn" 
                                data-url="${article.url}" data-title="${article.title}">
                                <i class="fas fa-file-alt me-1"></i>Summarize
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            newsRow.appendChild(articleCard);
        });
        
        newsContainer.appendChild(newsRow);
        
        // Add event listeners to summarize buttons
        document.querySelectorAll('.summarize-btn').forEach(button => {
            button.addEventListener('click', function() {
                summarizeArticle(this.dataset.url, this.dataset.title);
            });
        });
    }
    
    // Function to display error message
    function displayError(message) {
        newsContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-exclamation-circle text-danger" style="font-size: 3rem;"></i>
                <h5 class="mt-3">${message}</h5>
                <button class="btn btn-outline-primary mt-3" id="retryNewsBtn">
                    <i class="fas fa-sync-alt me-2"></i>Try Again
                </button>
            </div>
        `;
        
        document.getElementById('retryNewsBtn').addEventListener('click', function() {
            fetchNews(newsCategorySelect.value);
        });
    }
    
    // Function to handle summarize button click
    function summarizeArticle(url, title) {
        // Show loading overlay
        document.getElementById('loadingOverlay').style.display = 'flex';
        
        // Create form data
        const formData = new FormData();
        formData.append('url', url);
        formData.append('language', 'en');
        formData.append('max_length', 150);
        
        // Submit to the summarize endpoint
        fetch('/news/summarize', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading overlay
            document.getElementById('loadingOverlay').style.display = 'none';
            
            if (data.success) {
                // Populate the summary area
                document.getElementById('url').value = url;
                
                if (document.getElementById('summaryText')) {
                    document.getElementById('summaryText').innerHTML = data.summary;
                }
                
                // Scroll to summary section
                document.querySelector('.summary-container').scrollIntoView({
                    behavior: 'smooth'
                });
            } else {
                // Show error in toast
                const toast = document.createElement('div');
                toast.className = 'custom-toast error-toast show';
                toast.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i> ${data.error || 'Failed to summarize article'}`;
                document.querySelector('.toast-container').appendChild(toast);
                
                // Auto-hide toast after 5 seconds
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 500);
                }, 5000);
            }
        })
        .catch(error => {
            // Hide loading overlay
            document.getElementById('loadingOverlay').style.display = 'none';
            console.error('Error summarizing article:', error);
            
            // Show error toast
            const toast = document.createElement('div');
            toast.className = 'custom-toast error-toast show';
            toast.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i> Failed to summarize article. Please try again.';
            document.querySelector('.toast-container').appendChild(toast);
            
            // Auto-hide toast after 5 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 500);
            }, 5000);
        });
    }
    
    // Add event listener to refresh button
    refreshNewsBtn.addEventListener('click', function() {
        fetchNews(newsCategorySelect.value);
    });
    
    // Add event listener to category select
    newsCategorySelect.addEventListener('change', function() {
        fetchNews(this.value);
    });
    
    // Initial fetch when page loads - with no category to get general news
    fetchNews();
});