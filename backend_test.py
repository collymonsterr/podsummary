
import requests
import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PodBriefAPITester:
    def __init__(self, base_url="https://2741a2ce-05d6-4231-a8fb-a5540c0f1367.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if not headers:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        logger.info(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                logger.info(f"✅ Passed - Status: {response.status_code}")
                return success, response.json() if response.content else {}
            else:
                logger.error(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            logger.error(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_status(self):
        """Test API root endpoint"""
        return self.run_test(
            "API Status",
            "GET",
            "",
            200
        )

    def test_channel_videos(self, channel_url):
        """Test channel videos endpoint"""
        success, response = self.run_test(
            f"Channel Videos for {channel_url}",
            "POST",
            "channel-videos",
            200,
            data={"channel_url": channel_url}
        )
        
        if success:
            # Validate response structure
            if "channel_name" not in response:
                logger.error("❌ Missing 'channel_name' in response")
                return False
            
            if "videos" not in response:
                logger.error("❌ Missing 'videos' in response")
                return False
            
            videos = response["videos"]
            if not isinstance(videos, list):
                logger.error("❌ 'videos' is not a list")
                return False
            
            # Check if we have 6 videos as expected
            if len(videos) != 6:
                logger.warning(f"⚠️ Expected 6 videos, got {len(videos)}")
            
            # Check video structure
            for i, video in enumerate(videos):
                if "title" not in video and "snippet" not in video:
                    logger.error(f"❌ Video {i} missing title/snippet")
                    return False
                
                if "link" not in video and "url" not in video:
                    logger.error(f"❌ Video {i} missing link/url")
                    return False
            
            logger.info(f"✅ Found {len(videos)} videos for channel: {response['channel_name']}")
            return True
        
        return False

    def test_summarize_video(self, video_url):
        """Test video summarization endpoint"""
        logger.info(f"Testing video summarization for {video_url}")
        
        try:
            response = requests.post(
                f"{self.api_url}/summarize",
                json={"youtube_url": video_url},
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for summarization
            )
            
            if response.status_code == 200:
                self.tests_passed += 1
                data = response.json()
                
                # Validate response structure
                if "transcript" not in data:
                    logger.error("❌ Missing 'transcript' in response")
                    return False
                
                if "summary" not in data:
                    logger.error("❌ Missing 'summary' in response")
                    return False
                
                if "video_id" not in data:
                    logger.error("❌ Missing 'video_id' in response")
                    return False
                
                logger.info(f"✅ Successfully summarized video: {data.get('title', 'Unknown Title')}")
                return True
            else:
                logger.error(f"❌ Failed - Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.tests_run += 1

    def test_invalid_channel_url(self):
        """Test error handling for invalid channel URL"""
        invalid_url = "https://www.youtube.com/invalid_channel_123456"
        
        # This should still return 200 but with empty videos or error message
        success, response = self.run_test(
            "Invalid Channel URL",
            "POST",
            "channel-videos",
            200,
            data={"channel_url": invalid_url}
        )
        
        # Even with invalid URL, the API should return a valid response
        # It might have empty videos array or error message
        if success:
            if "videos" in response and len(response["videos"]) == 0:
                logger.info("✅ API correctly returned empty videos array for invalid channel")
                return True
            elif "error" in response:
                logger.info("✅ API correctly returned error message for invalid channel")
                return True
            else:
                logger.warning("⚠️ API returned unexpected response for invalid channel")
                return False
        
        return False

    def test_invalid_video_url(self):
        """Test error handling for invalid video URL"""
        invalid_url = "https://www.youtube.com/watch?v=invalid_video_id"
        
        try:
            response = requests.post(
                f"{self.api_url}/summarize",
                json={"youtube_url": invalid_url},
                headers={'Content-Type': 'application/json'}
            )
            
            # Should return 400 or 500 for invalid video
            if response.status_code in [400, 500]:
                logger.info(f"✅ API correctly returned error {response.status_code} for invalid video URL")
                self.tests_passed += 1
                return True
            else:
                logger.error(f"❌ API returned unexpected status {response.status_code} for invalid video URL")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed - Error: {str(e)}")
            return False
        finally:
            self.tests_run += 1

def main():
    # Setup
    tester = PodBriefAPITester()
    
    # Test API status
    api_status_success, _ = tester.test_api_status()
    if not api_status_success:
        logger.error("❌ API status check failed, stopping tests")
        return 1
    
    # Test channel videos with different URL formats
    channel_urls = [
        "https://www.youtube.com/@Fireship",
        "https://www.youtube.com/c/TheOffice",
        "https://www.youtube.com/user/CollegeHumor"
    ]
    
    channel_success = True
    for url in channel_urls:
        if not tester.test_channel_videos(url):
            channel_success = False
            logger.error(f"❌ Channel videos test failed for {url}")
    
    if not channel_success:
        logger.warning("⚠️ Some channel tests failed, continuing with other tests")
    
    # Test invalid channel URL
    tester.test_invalid_channel_url()
    
    # Test invalid video URL
    tester.test_invalid_video_url()
    
    # Test video summarization (only if channel tests passed)
    if channel_success:
        # Get a video URL from one of the channels
        logger.info("Testing video summarization...")
        success, response = tester.run_test(
            "Get Channel Videos for Summarization Test",
            "POST",
            "channel-videos",
            200,
            data={"channel_url": channel_urls[0]}  # Use first channel
        )
        
        if success and "videos" in response and len(response["videos"]) > 0:
            # Get the first video URL
            video = response["videos"][0]
            video_url = video.get("link") or video.get("url")
            
            if video_url:
                tester.test_summarize_video(video_url)
    
    # Print results
    logger.info(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
