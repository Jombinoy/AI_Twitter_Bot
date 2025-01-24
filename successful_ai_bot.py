import os
import json
import time
import logging
from datetime import datetime, timezone
import tweepy
import google.generativeai as genai
from typing import Dict, List, Optional
import random
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ai_technology_bot.log'
)

class SuccessfulAIBot:
    def __init__(self):
        # Ensure .env is loaded
        load_dotenv(override=True)
        
        # Twitter API credentials from environment variables with validation
        credentials = {
            'TWITTER_API_KEY': os.getenv('TWITTER_API_KEY'),
            'TWITTER_API_SECRET': os.getenv('TWITTER_API_SECRET'),
            'TWITTER_ACCESS_TOKEN': os.getenv('TWITTER_ACCESS_TOKEN'),
            'TWITTER_ACCESS_TOKEN_SECRET': os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
        }
        
        # Log environment variable status
        logging.info("Checking environment variables...")
        missing_vars = []
        for key, value in credentials.items():
            if not value:
                missing_vars.append(key)
                logging.error(f"Missing environment variable: {key}")
            else:
                logging.info(f"Found environment variable: {key}")
        
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please check:\n"
                "1. Your .env file exists in the project root directory\n"
                "2. The .env file contains all required variables\n"
                "3. There are no typos in variable names\n"
                "4. Values are properly formatted (no quotes, no spaces around =)"
            )
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Store credentials
        self.twitter_api_key = credentials['TWITTER_API_KEY']
        self.twitter_api_secret = credentials['TWITTER_API_SECRET']
        self.twitter_access_token = credentials['TWITTER_ACCESS_TOKEN']
        self.twitter_access_token_secret = credentials['TWITTER_ACCESS_TOKEN_SECRET']
        self.twitter_bearer_token = credentials['TWITTER_BEARER_TOKEN']
        
        # Initialize Gemini AI
        genai.configure(api_key=credentials['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Verify Twitter credentials
        logging.info("Verifying Twitter credentials...")
        success, message = self.verify_credentials(
            self.twitter_api_key,
            self.twitter_api_secret,
            self.twitter_access_token,
            self.twitter_access_token_secret,
            self.twitter_bearer_token
        )
        
        if not success:
            raise ValueError(f"Twitter credentials verification failed: {message}")
        
        logging.info(message)  # Log successful verification message

        # Initialize Twitter client
        try:
            logging.info("Initializing Twitter client...")
            self.client = tweepy.Client(
                bearer_token=self.twitter_bearer_token,
                consumer_key=self.twitter_api_key,
                consumer_secret=self.twitter_api_secret,
                access_token=self.twitter_access_token,
                access_token_secret=self.twitter_access_token_secret,
                wait_on_rate_limit=True
            )
        except Exception as e:
            error_msg = f"Error initializing Twitter client: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Initialize interaction tracking
        self.interactions_file = "ai_technology_interactions.json"
        self.interactions = self.load_interactions()
        
        # Create empty interactions file if it doesn't exist
        if not os.path.exists(self.interactions_file):
            self.save_interactions()

    @staticmethod
    def verify_credentials(api_key, api_secret, access_token, access_token_secret, bearer_token):
        """Verify Twitter credentials and return detailed error messages"""
        try:
            # First try OAuth 1.0a authentication
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            me = client.get_me()
            return True, f"Credentials verified successfully. Connected as @{me.data.username}"
        except tweepy.errors.Unauthorized as e:
            # Try bearer token separately to identify which credentials are invalid
            try:
                client = tweepy.Client(bearer_token=bearer_token)
                client.get_me()
                return False, "OAuth 1.0a credentials are invalid, but Bearer token is valid. Please check your API key and Access token."
            except tweepy.errors.Unauthorized:
                return False, "All credentials are invalid. Please regenerate your API keys and tokens."
            except Exception as e:
                return False, f"Bearer token verification failed: {str(e)}"
        except Exception as e:
            return False, f"Credential verification failed: {str(e)}"

    def load_interactions(self) -> Dict:
        """Load interaction history"""
        try:
            with open(self.interactions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "tweets_posted": [],
                "replies_sent": [],
                "likes_given": [],
                "follows_made": []
            }

    def save_interactions(self):
        """Save interactions to file"""
        with open(self.interactions_file, 'w', encoding='utf-8') as f:
            json.dump(self.interactions, f, indent=4, ensure_ascii=False)

    def generate_tweet(self) -> str:
        """Generate an AI-focused tweet"""
        tweet_templates = [
            "💡 Dive into the world of AI! {topic} {hashtags}",
            "🤖 Unlock the power of #AI! {topic} {hashtags}",
            "💡 Unleash the Power of #AITechnology! {topic} {hashtags}",
            "🌟 The future is here with AI! {topic} {hashtags}"
        ]
        
        topics = [
            "From healthcare to finance, AI is revolutionizing how we solve complex problems.",
            "From self-driving cars to medical breakthroughs, AI is transforming industries and empowering humans.",
            "AI is reshaping industries, improving efficiency, and empowering innovation.",
            "Discover how AI is creating endless possibilities and shaping our tomorrow."
        ]
        
        hashtags = [
            "#AIRevolution #FutureTech",
            "#ArtificialIntelligence #Innovation",
            "#AITech #DigitalTransformation",
            "#TechInnovation #AIFuture"
        ]

        template = random.choice(tweet_templates)
        topic = random.choice(topics)
        hashtag = random.choice(hashtags)
        
        tweet = template.format(topic=topic, hashtags=hashtag)
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
            
        return tweet

    def generate_reply(self, tweet_text: str) -> str:
        """Generate a contextual reply"""
        prompt = f"""
        Generate a thoughtful reply to this tweet about AI technology:
        "{tweet_text}"
        Requirements:
        1. Keep it under 240 characters (to leave room for mentions)
        2. Make it insightful and professional
        3. Focus on the specific topic mentioned
        4. Add value to the conversation
        """
        
        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip().replace('"', '').replace("'", "")
            return reply[:240]  # Shorter limit to ensure space for mentions
        except Exception as e:
            logging.error(f"Error generating reply: {str(e)}")
            return None

    def post_tweet(self):
        """Post a tweet and track it"""
        tweet_text = self.generate_tweet()
        try:
            # Verify credentials before posting
            try:
                self.client.get_me()
            except tweepy.errors.Unauthorized:
                error_msg = "Twitter credentials are invalid. Please check your API keys and tokens."
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            response = self.client.create_tweet(text=tweet_text)
            
            if response and response.data:
                tweet_id = response.data['id']
                self.interactions["tweets_posted"].append({
                    "id": tweet_id,
                    "text": tweet_text,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                self.save_interactions()
                logging.info(f"Successfully posted tweet (ID: {tweet_id}): {tweet_text}")
                # Add delay after posting
                time.sleep(60)
                return response
            else:
                logging.error("Failed to post tweet: No response data")
                return None
                
        except tweepy.errors.TooManyRequests:
            logging.error("Rate limit exceeded. Waiting before retrying...")
            time.sleep(900)  # 15 minutes cooldown
            return None
        except tweepy.errors.Forbidden as e:
            logging.error(f"Forbidden action when posting tweet: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error posting tweet: {str(e)}")
            return None

    def interact_with_tweet(self, tweet):
        """Interact with a single tweet"""
        try:
            # Generate and send reply
            reply_text = self.generate_reply(tweet.text)
            if reply_text:
                reply = self.client.create_tweet(
                    text=reply_text,
                    in_reply_to_tweet_id=tweet.id
                )
                
                self.interactions["replies_sent"].append({
                    "original_tweet_id": tweet.id,
                    "reply_text": reply_text,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                logging.info(f"Posted reply to tweet {tweet.id}")
                
                # Add delay after replying
                time.sleep(30)
            
            # Like the tweet
            self.client.like(tweet.id)
            self.interactions["likes_given"].append({
                "tweet_id": tweet.id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logging.info(f"Liked tweet {tweet.id}")
            
            # Add delay after liking
            time.sleep(30)
            
            # Follow the user
            self.client.follow_user(tweet.author_id)
            self.interactions["follows_made"].append({
                "user_id": tweet.author_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logging.info(f"Followed user {tweet.author_id}")
            
            # Save after each successful interaction
            self.save_interactions()
            
            # Add delay after following
            time.sleep(30)
            
        except Exception as e:
            logging.error(f"Error during interaction with tweet {tweet.id}: {str(e)}")

    def find_and_interact(self):
        """Find relevant tweets and interact with them"""
        search_queries = [
            "#AI -is:retweet lang:en",
            "#ArtificialIntelligence -is:retweet lang:en",
            "#MachineLearning -is:retweet lang:en"
        ]
        
        for query in search_queries:
            try:
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=5,  # Reduced from 10 to avoid rate limits
                    tweet_fields=['author_id', 'conversation_id']
                )
                
                if not tweets.data:
                    continue
                
                for tweet in tweets.data:
                    self.interact_with_tweet(tweet)
                    # Add longer delay between different tweets
                    time.sleep(60)
                
                # Add delay between different search queries
                time.sleep(120)
                
            except Exception as e:
                logging.error(f"Error in tweet search: {str(e)}")
                time.sleep(900)  # 15 minutes cooldown on error
                continue

    def run(self):
        """Main bot loop"""
        logging.info("Starting Successful AI Bot...")
        
        while True:
            try:
                # Post a new tweet
                self.post_tweet()
                
                # Wait before starting interactions
                time.sleep(300)  # 5 minutes
                
                # Find and interact with relevant tweets
                self.find_and_interact()
                
                # Wait longer between cycles
                logging.info("Completed interaction cycle, waiting for next cycle...")
                time.sleep(7200)  # 2 hours
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(900)  # 15 minutes cooldown on error

if __name__ == "__main__":
    bot = SuccessfulAIBot()
    bot.run()
