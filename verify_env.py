import os
import logging
from dotenv import load_dotenv
import tweepy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def verify_env_file():
    """Verify the .env file and its contents"""
    # Check if .env file exists
    if not os.path.exists('.env'):
        logging.error("❌ .env file not found in the current directory")
        return False
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Required variables
    required_vars = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET',
        'TWITTER_BEARER_TOKEN',
        'GEMINI_API_KEY'
    ]
    
    # Check each variable
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            logging.error(f"❌ Missing or empty: {var}")
        else:
            logging.info(f"✓ Found: {var}")
    
    if missing_vars:
        logging.error("\n❌ Some required variables are missing. Please check your .env file.")
        return False
    
    # Verify Twitter credentials
    try:
        logging.info("\nVerifying Twitter credentials...")
        client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        me = client.get_me()
        logging.info(f"✓ Twitter credentials verified! Connected as @{me.data.username}")
        return True
        
    except tweepy.errors.Unauthorized as e:
        logging.error(f"\n❌ Twitter authentication failed: {str(e)}")
        logging.error("\nPlease check:")
        logging.error("1. Your Twitter app has 'Read and Write' permissions")
        logging.error("2. Your credentials are correct and not expired")
        logging.error("3. You're using OAuth 1.0a tokens (not OAuth 2.0)")
        return False
        
    except Exception as e:
        logging.error(f"\n❌ Error verifying credentials: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n=== Twitter Bot Environment Verification ===\n")
    if verify_env_file():
        print("\n✓ All checks passed! Your environment is properly configured.")
    else:
        print("\n❌ Environment verification failed. Please fix the issues above.")
