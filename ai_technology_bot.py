import os
import json
import time
import logging
from datetime import datetime
import tweepy
import google.generativeai as genai
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ai_technology_bot.log'
)

class AITechnologyBot:
    def __init__(self):
        # Initialize Twitter API credentials
        self.twitter_api_key = "dV5CX3GJqSwINg3KEa4Gj176Y"
        self.twitter_api_secret = "x8gZh4mt22caUQ6N6TzD65GYbhKNGGiBlV5tDlQrJYtjUXzC3b"
        self.twitter_access_token = "1867436005206503428-qvNAHpoqSE0tX0ZXclo1ryOKYvcAzC"
        self.twitter_access_token_secret = "X2hhH7B8DFwgKx7CvPmLOXJr3hNJ47h2vN5rkLqN15Ha8"
        self.twitter_bearer_token = "AAAAAAAAAAAAAAAAAAAAANcTxgEAAAAAlMhbHiQhSIYmiH3xKzH4rIa1Xvg%3DMPbdXMlPEhDuKmoVgJF7f3gOXuXFlmRrMpggZrN3Kxo8shiQJU"

        # Initialize Gemini AI
        genai.configure(api_key="AIzaSyDhMmtJsw7Y2MSzo0GgAJMmNS-6qqlP5Ps")
        self.model = genai.GenerativeModel('gemini-pro')

        # Initialize Twitter client
        self.client = tweepy.Client(
            bearer_token=self.twitter_bearer_token,
            consumer_key=self.twitter_api_key,
            consumer_secret=self.twitter_api_secret,
            access_token=self.twitter_access_token,
            access_token_secret=self.twitter_access_token_secret,
            wait_on_rate_limit=True
        )

        # Load interaction history
        self.interactions_file = "ai_technology_interactions.json"
        self.interactions = self.load_interactions()

    def load_interactions(self) -> Dict:
        """Load interaction history from JSON file"""
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
        """Save interactions to JSON file"""
        with open(self.interactions_file, 'w', encoding='utf-8') as f:
            json.dump(self.interactions, f, indent=4, ensure_ascii=False)

    def generate_tweet(self) -> str:
        """Generate a tweet about AI technology using Gemini AI"""
        prompts = [
            "Generate an engaging tweet about AI technology and its impact. Include relevant hashtags and emojis.",
            "Create an inspiring tweet about how AI is transforming industries. Use appropriate hashtags and emojis.",
            "Write a thought-provoking tweet about the future of AI. Include trending hashtags and suitable emojis."
        ]
        
        for prompt in prompts:
            try:
                response = self.model.generate_content(prompt)
                tweet = response.text.strip().replace('"', '').replace("'", "")
                if len(tweet) <= 280:
                    return tweet
            except Exception as e:
                logging.error(f"Error generating tweet: {str(e)}")
                continue
        
        return "🤖 AI is revolutionizing our world! From healthcare to finance, artificial intelligence is creating endless possibilities. Join the #AIRevolution and embrace the future! #TechInnovation #AI"

    def post_tweet(self):
        """Post a tweet and track it"""
        tweet_text = self.generate_tweet()
        try:
            response = self.client.create_tweet(text=tweet_text)
            
            self.interactions["tweets_posted"].append({
                "text": tweet_text,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.save_interactions()
            logging.info(f"Posted tweet: {tweet_text}")
            return response
        except Exception as e:
            logging.error(f"Error posting tweet: {str(e)}")
            return None

    def generate_reply(self, tweet_text: str) -> str:
        """Generate a contextual reply using Gemini AI"""
        prompt = f"""
        Generate a thoughtful reply to this tweet about AI technology:
        "{tweet_text}"
        Requirements:
        - Keep it under 280 characters
        - Make it engaging and professional
        - Add value to the conversation
        - Focus on AI technology
        """
        
        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip().replace('"', '').replace("'", "")
            return reply[:280]
        except Exception as e:
            logging.error(f"Error generating reply: {str(e)}")
            return None

    def interact_with_tweets(self):
        """Search and interact with relevant tweets"""
        search_queries = [
            "#AI -is:retweet",
            "#ArtificialIntelligence -is:retweet",
            "#MachineLearning -is:retweet",
            "artificial intelligence -is:retweet"
        ]
        
        for query in search_queries:
            try:
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=['author_id']
                )
                
                if not tweets.data:
                    continue
                
                for tweet in tweets.data:
                    # Generate and send reply
                    reply_text = self.generate_reply(tweet.text)
                    if reply_text:
                        try:
                            reply = self.client.create_tweet(
                                text=reply_text,
                                in_reply_to_tweet_id=tweet.id
                            )
                            
                            self.interactions["replies_sent"].append({
                                "original_tweet_id": tweet.id,
                                "reply_text": reply_text,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except Exception as e:
                            logging.error(f"Error replying to tweet: {str(e)}")
                    
                    # Like the tweet
                    try:
                        self.client.like(tweet.id)
                        self.interactions["likes_given"].append({
                            "tweet_id": tweet.id,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logging.error(f"Error liking tweet: {str(e)}")
                    
                    # Follow the user
                    try:
                        self.client.follow_user(tweet.author_id)
                        self.interactions["follows_made"].append({
                            "user_id": tweet.author_id,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logging.error(f"Error following user: {str(e)}")
                    
                    self.save_interactions()
                    time.sleep(60)  # Rate limiting
            
            except Exception as e:
                logging.error(f"Error in tweet interaction: {str(e)}")
                continue

    def run(self):
        """Main bot loop"""
        logging.info("Starting AI Technology Bot...")
        
        while True:
            try:
                # Post a new tweet
                self.post_tweet()
                logging.info("Posted new tweet")
                
                # Interact with other tweets
                self.interact_with_tweets()
                logging.info("Completed interaction cycle")
                
                # Wait before next cycle (2 hours)
                time.sleep(7200)
                
            except Exception as e:
                logging.error(f"Error in main loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    bot = AITechnologyBot()
    bot.run()
