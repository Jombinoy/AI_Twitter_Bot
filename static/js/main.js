document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startBot');
    const stopButton = document.getElementById('stopBot');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const logContainer = document.getElementById('logContainer');
    const tweetsContainer = document.getElementById('tweetsContainer');
    const loadMoreTweetsButton = document.getElementById('loadMoreTweets');
    
    let botRunning = false;
    let currentPage = 1;
    const tweetsPerPage = 10;
    
    // Update UI elements
    function updateBotStatus(running) {
        botRunning = running;
        statusDot.classList.toggle('active', running);
        statusText.textContent = running ? 'Bot Active' : 'Bot Inactive';
        startButton.disabled = running;
        stopButton.disabled = !running;
    }
    
    // Format date
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    // Create tweet card
    function createTweetCard(tweet) {
        const card = document.createElement('div');
        card.className = 'tweet-card';
        
        const botAvatar = 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png';
        
        card.innerHTML = `
            <div class="tweet-header">
                <img class="tweet-avatar" src="${botAvatar}" alt="Profile">
                <div class="tweet-user-info">
                    <div class="tweet-username">${tweet.user_name}</div>
                    <div class="tweet-handle">@${tweet.user_screen_name}</div>
                </div>
                <div class="tweet-timestamp">${formatDate(tweet.timestamp)}</div>
            </div>
            <div class="tweet-content">
                ${tweet.type === 'reply' ? '<span class="reply-badge">Reply</span>' : ''}
                ${tweet.tweet_text}
            </div>
            ${tweet.type === 'reply' ? `
                <div class="tweet-reply">
                    <div class="tweet-reply-header">In reply to Tweet ID: ${tweet.original_tweet_id}</div>
                </div>
            ` : ''}
        `;
        
        return card;
    }
    
    // Load tweets
    function loadTweets(page = 1) {
        fetch(`/api/tweets?page=${page}&per_page=${tweetsPerPage}`)
            .then(response => response.json())
            .then(data => {
                if (page === 1) {
                    tweetsContainer.innerHTML = '';
                }
                
                data.tweets.forEach(tweet => {
                    tweetsContainer.appendChild(createTweetCard(tweet));
                });
                
                loadMoreTweetsButton.style.display = data.has_more ? 'block' : 'none';
                currentPage = page;
            })
            .catch(error => console.error('Error loading tweets:', error));
    }
    
    // Add log entry with type
    function addLogEntry(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        
        // Parse tweet content if present
        let formattedMessage = message;
        if (message.includes('Successfully posted tweet:')) {
            const tweetContent = message.split('Successfully posted tweet:')[1].trim();
            formattedMessage = `Posted Tweet: <span class="tweet-preview">${tweetContent}</span>`;
        }
        
        entry.innerHTML = `
            <span class="timestamp">${new Date().toLocaleTimeString()}</span>
            <span class="message ${type}">${formattedMessage}</span>
        `;
        logContainer.insertBefore(entry, logContainer.firstChild);
        
        // Keep only last 50 entries to prevent too much memory usage
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.lastChild);
        }
    }
    
    // Update statistics
    function updateStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalInteractions').textContent = data.total_interactions;
                document.getElementById('todayTweets').textContent = data.today_tweets;
                document.getElementById('responseRate').textContent = data.response_rate + '%';
            })
            .catch(error => console.error('Error fetching stats:', error));
    }
    
    // Start bot
    startButton.addEventListener('click', function() {
        startButton.disabled = true; // Prevent double-clicks
        fetch('/api/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBotStatus(true);
                    addLogEntry('Bot started successfully', 'success');
                } else {
                    addLogEntry(`Failed to start bot: ${data.message}`, 'error');
                    updateBotStatus(false);
                }
            })
            .catch(error => {
                console.error('Error starting bot:', error);
                addLogEntry('Failed to start bot: Network error', 'error');
                updateBotStatus(false);
            })
            .finally(() => {
                startButton.disabled = false;
            });
    });
    
    // Stop bot
    stopButton.addEventListener('click', function() {
        stopButton.disabled = true; // Prevent double-clicks
        fetch('/api/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBotStatus(false);
                    addLogEntry('Bot stopped successfully', 'warning');
                } else {
                    addLogEntry(`Failed to stop bot: ${data.message}`, 'error');
                    updateBotStatus(true);
                }
            })
            .catch(error => {
                console.error('Error stopping bot:', error);
                addLogEntry('Failed to stop bot: Network error', 'error');
                // Keep current status on error
            })
            .finally(() => {
                stopButton.disabled = false;
            });
    });
    
    // Load more tweets
    loadMoreTweetsButton.addEventListener('click', function() {
        loadTweets(currentPage + 1);
    });
    
    // Initialize
    updateBotStatus(false);
    loadTweets(1);
    
    // Poll for updates every 30 seconds
    setInterval(() => {
        updateStats();
        if (currentPage === 1) {
            loadTweets(1);
        }
    }, 30000);
});
