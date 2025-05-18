
import requests
import sys
import time
import logging
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeSummarizerTester:
    def __init__(self, base_url="https://03994ffd-b1ec-4917-9c69-f797154b536c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        self.invalid_video_url = "https://www.youtube.com/watch?v=invalid"

    def run_test(self, name, method, endpoint, expected_status, data=None, validate_func=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        logger.info(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                logger.info(f"✅ Passed - Status: {response.status_code}")
                
                if validate_func and callable(validate_func):
                    validation_result = validate_func(response)
                    if not validation_result:
                        success = False
                        self.tests_passed -= 1
                        logger.error("❌ Validation failed")
            else:
                logger.error(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    logger.error(f"Response: {response.text[:500]}")

            return success, response

        except Exception as e:
            logger.error(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_api_status(self):
        """Test the API status endpoint"""
        return self.run_test(
            "API Status Check",
            "GET",
            "",
            200
        )

    def test_invalid_youtube_url(self):
        """Test summarizing an invalid YouTube URL"""
        return self.run_test(
            "Summarize Invalid YouTube URL",
            "POST",
            "summarize",
            400,
            data={"url": self.invalid_video_url}
        )

    def test_valid_youtube_url(self):
        """Test summarizing a valid YouTube URL"""
        logger.info("\n⏳ Testing video summarization (this may take a minute)...")
        
        success, response = self.run_test(
            "Summarize Valid YouTube URL",
            "POST",
            "summarize",
            200,
            data={"url": self.test_video_url}
        )
        
        if success:
            try:
                data = response.json()
                
                # Validate response structure
                logger.info("\n🔍 Validating transcript and summary content...")
                
                # Check if transcript exists and is not empty
                has_transcript = 'transcript' in data and data['transcript']
                if has_transcript:
                    logger.info("✅ Transcript is not empty")
                else:
                    logger.error("❌ Transcript is empty or missing")
                    success = False
                
                # Check if summary exists and is not empty
                has_summary = 'summary' in data and data['summary']
                if has_summary:
                    logger.info("✅ Summary is not empty")
                else:
                    logger.error("❌ Summary is empty or missing")
                    success = False
                
                # Extract video ID from URL
                parsed_url = urlparse(self.test_video_url)
                video_id = parse_qs(parsed_url.query).get('v', [''])[0]
                
                if video_id:
                    logger.info(f"✅ Valid video ID: {video_id}")
                    logger.info(f"✅ Valid URL: {self.test_video_url}")
                else:
                    logger.error("❌ Could not extract video ID from URL")
                    success = False
                
                # Check if summary is shorter than transcript (as expected)
                if has_transcript and has_summary:
                    transcript_length = len(data['transcript'])
                    summary_length = len(data['summary'])
                    
                    if summary_length < transcript_length:
                        logger.info("✅ Summary is shorter than transcript (as expected)")
                        logger.info(f"📏 Transcript length: {transcript_length} characters")
                        logger.info(f"📏 Summary length: {summary_length} characters")
                    else:
                        logger.warning("⚠️ Summary is not shorter than transcript")
                        logger.info(f"📏 Transcript length: {transcript_length} characters")
                        logger.info(f"📏 Summary length: {summary_length} characters")
                
            except Exception as e:
                logger.error(f"❌ Error validating response: {str(e)}")
                success = False
        
        return success, response

    def test_get_history(self):
        """Test getting the summary history"""
        success, response = self.run_test(
            "Get Summary History",
            "GET",
            "history",
            200
        )
        
        if success:
            try:
                data = response.json()
                history_items = data.get('history', [])
                
                logger.info(f"📚 History items: {len(history_items)}")
                
                if history_items:
                    # Get the most recent item
                    most_recent = history_items[0]
                    logger.info(f"📅 Most recent summary: {most_recent.get('url')} ({most_recent.get('video_id')})")
                else:
                    logger.warning("⚠️ No history items found")
                
            except Exception as e:
                logger.error(f"❌ Error validating history response: {str(e)}")
                success = False
        
        return success, response

def main():
    print("=" * 80)
    print("🧪 YOUTUBE VIDEO SUMMARIZER API TEST SUITE 🧪")
    print("=" * 80)
    
    tester = YouTubeSummarizerTester()
    
    # Run tests
    api_status_success, _ = tester.test_api_status()
    invalid_url_success, _ = tester.test_invalid_youtube_url()
    valid_url_success, _ = tester.test_valid_youtube_url()
    history_success, _ = tester.test_get_history()
    
    # Print results
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 80)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
