from flask import Flask, render_template, jsonify, request
from successful_ai_bot import SuccessfulAIBot
import threading
import json
from datetime import datetime
import math
import time

app = Flask(__name__)
bot = SuccessfulAIBot()
bot_thread = None
bot_running = False

class LogHandler:
    def __init__(self):
        self.logs = []
        self.max_logs = 100

    def add_log(self, message, level='INFO'):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        self.logs.insert(0, log_entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop()

log_handler = LogHandler()

def run_bot():
    global bot_running
    while bot_running:
        try:
            log_handler.add_log("Bot iteration started", "INFO")
            bot.run()
            # Add a small delay between iterations to prevent overwhelming the API
            time.sleep(1)
        except Exception as e:
            error_msg = f"Bot error: {str(e)}"
            print(error_msg)
            log_handler.add_log(error_msg, "ERROR")
            bot_running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tweets')
def get_tweets():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        with open('ai_technology_interactions.json', 'r') as f:
            data = json.load(f)
        
        # Combine tweets_posted and replies_sent into a single list
        tweets_list = []
        
        # Add posted tweets
        for tweet in data.get('tweets_posted', []):
            tweets_list.append({
                'tweet_text': tweet.get('text', ''),
                'timestamp': tweet.get('timestamp', ''),
                'user_name': 'AI Technology Bot',
                'user_screen_name': 'AITechBot',
                'type': 'posted'
            })
        
        # Add replies
        for reply in data.get('replies_sent', []):
            tweets_list.append({
                'tweet_text': reply.get('reply_text', ''),
                'timestamp': reply.get('timestamp', ''),
                'original_tweet_id': reply.get('original_tweet_id', ''),
                'user_name': 'AI Technology Bot',
                'user_screen_name': 'AITechBot',
                'type': 'reply'
            })
        
        # Sort by timestamp
        tweets_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        total_pages = math.ceil(len(tweets_list) / per_page)
        
        # Get tweets for current page
        page_tweets = tweets_list[start_idx:end_idx]
        
        return jsonify({
            'tweets': page_tweets,
            'page': page,
            'total_pages': total_pages,
            'has_more': page < total_pages
        })
    except Exception as e:
        print(f"Error fetching tweets: {str(e)}")
        return jsonify({
            'tweets': [],
            'page': 1,
            'total_pages': 1,
            'has_more': False
        })

@app.route('/api/start', methods=['POST'])
def start_bot():
    global bot_thread, bot_running
    
    try:
        if not bot_running:
            # Initialize bot with enhanced error handling
            try:
                bot.client.get_me()  # Verify Twitter connection
            except ConnectionError as e:
                error_msg = f"Network error: Unable to connect to Twitter API. Please check your internet connection. Error: {str(e)}"
                log_handler.add_log(error_msg, "ERROR")
                return jsonify({'success': False, 'message': error_msg})
            except ValueError as e:
                error_msg = f"Authentication error: {str(e)}"
                log_handler.add_log(error_msg, "ERROR")
                return jsonify({'success': False, 'message': error_msg})
            except Exception as e:
                error_msg = f"Unexpected error during bot initialization: {str(e)}"
                log_handler.add_log(error_msg, "ERROR")
                return jsonify({'success': False, 'message': error_msg})
            
            # Start bot if verification successful
            bot_running = True
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            log_handler.add_log("Bot started successfully", "INFO")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Bot is already running'})
    except Exception as e:
        error_msg = f"Error starting bot: {str(e)}"
        log_handler.add_log(error_msg, "ERROR")
        return jsonify({'success': False, 'message': error_msg})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global bot_running, bot_thread
    
    try:
        if bot_running:
            bot_running = False
            if bot_thread and bot_thread.is_alive():
                # Give the thread a chance to finish gracefully
                bot_thread.join(timeout=5)
            log_handler.add_log("Bot stopped successfully", "INFO")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Bot is not running'})
    except Exception as e:
        error_msg = f"Error stopping bot: {str(e)}"
        log_handler.add_log(error_msg, "ERROR")
        return jsonify({'success': False, 'message': error_msg})

@app.route('/api/stats')
def get_stats():
    try:
        with open('ai_technology_interactions.json', 'r') as f:
            data = json.load(f)
        
        # Get total interactions
        total_tweets = len(data.get('tweets_posted', []))
        total_replies = len(data.get('replies_sent', []))
        total_interactions = total_tweets + total_replies
        
        # Get today's tweets
        today = datetime.now().date()
        today_tweets = sum(1 for tweet in data.get('tweets_posted', [])
                         if datetime.fromisoformat(tweet['timestamp']).date() == today)
        today_replies = sum(1 for reply in data.get('replies_sent', [])
                          if datetime.fromisoformat(reply['timestamp']).date() == today)
        
        # Calculate response rate (replies / total interactions)
        response_rate = round((total_replies / total_interactions * 100) if total_interactions > 0 else 0)
        
        return jsonify({
            'total_interactions': total_interactions,
            'today_tweets': today_tweets + today_replies,
            'response_rate': response_rate
        })
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")
        return jsonify({
            'total_interactions': 0,
            'today_tweets': 0,
            'response_rate': 0
        })

@app.route('/api/logs')
def get_logs():
    try:
        return jsonify({
            'logs': log_handler.logs
        })
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")
        return jsonify({
            'logs': []
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
