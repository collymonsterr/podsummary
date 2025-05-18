
import requests
import sys
import time
import logging
import re
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
        
        # Test videos
        self.music_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        self.comedy_sketch_url = "https://www.youtube.com/watch?v=THNPmhBl-8I"  # Mitchell and Webb - Brain Surgery
        self.ted_talk_url = "https://www.youtube.com/watch?v=_vS_b7cJn2A"  # TED talk
        self.educational_video_url = "https://www.youtube.com/watch?v=8S0FDjFBj8o"  # Educational video
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
            data={"youtube_url": self.invalid_video_url}
        )

    def test_valid_youtube_url(self, video_url, video_type):
        """Test summarizing a valid YouTube URL"""
        logger.info(f"\n⏳ Testing {video_type} video summarization (this may take a minute)...")
        
        success, response = self.run_test(
            f"Summarize {video_type} Video",
            "POST",
            "summarize",
            200,
            data={"youtube_url": video_url}
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
                    
                    # Check for emojis in the summary
                    emoji_pattern = re.compile(r'[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF2702-27B024C2-\U0001F251\U0001f926-\U0001f937]')
                    emojis_found = emoji_pattern.findall(data['summary'])
                    
                    if emojis_found:
                        logger.info(f"✅ Found {len(emojis_found)} emojis in summary: {''.join(emojis_found[:10])}")
                    else:
                        logger.warning("⚠️ No emojis found in summary")
                        
                    # Special check for music videos
                    if video_url == self.music_video_url:
                        if "🎵" in data['summary'] or "🎶" in data['summary'] or "🎤" in data['summary']:
                            logger.info("✅ Music video has music-related emojis in summary")
                        else:
                            logger.warning("⚠️ Music video summary doesn't have music-related emojis")
                else:
                    logger.error("❌ Summary is empty or missing")
                    success = False
                
                # Extract video ID from URL
                parsed_url = urlparse(video_url)
                video_id = parse_qs(parsed_url.query).get('v', [''])[0]
                
                if video_id:
                    logger.info(f"✅ Valid video ID: {video_id}")
                    logger.info(f"✅ Valid URL: {video_url}")
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
                
                # Print a sample of the transcript and summary for verification
                if has_transcript:
                    transcript_sample = data['transcript'][:200] + "..." if len(data['transcript']) > 200 else data['transcript']
                    logger.info(f"📝 Transcript sample: {transcript_sample}")
                
                if has_summary:
                    summary_sample = data['summary'][:200] + "..." if len(data['summary']) > 200 else data['summary']
                    logger.info(f"📝 Summary sample: {summary_sample}")
                
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
                history_items = response.json()
                
                logger.info(f"📚 History items: {len(history_items)}")
                
                if history_items:
                    # Get the most recent item
                    most_recent = history_items[0]
                    logger.info(f"📅 Most recent summary: {most_recent.get('url')} ({most_recent.get('video_id')})")
                    
                    # Check for emojis in the most recent summary
                    if 'summary' in most_recent and most_recent['summary']:
                        emoji_pattern = re.compile(r'[\U0001F300-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF2702-27B024C2-\U0001F251\U0001f926-\U0001f937]')
                        emojis_found = emoji_pattern.findall(most_recent['summary'])
                        
                        if emojis_found:
                            logger.info(f"✅ Found {len(emojis_found)} emojis in history summary: {''.join(emojis_found[:10])}")
                        else:
                            logger.warning("⚠️ No emojis found in history summary")
                else:
                    logger.warning("⚠️ No history items found")
                
            except Exception as e:
                logger.error(f"❌ Error validating history response: {str(e)}")
                success = False
        
        return success, response
        
    def test_caching_functionality(self, video_url):
        """Test that caching works correctly for previously summarized videos"""
        logger.info("\n🔍 Testing caching functionality...")
        
        # First request - should not be cached
        logger.info("Making first request to summarize video (should not be cached)...")
        first_success, first_response = self.run_test(
            "First Summarization Request",
            "POST",
            "summarize",
            200,
            data={"youtube_url": video_url}
        )
        
        if not first_success:
            logger.error("❌ First summarization request failed, cannot test caching")
            return False, None
        
        first_data = first_response.json()
        first_is_cached = first_data.get('is_cached', False)
        
        if first_is_cached:
            logger.warning("⚠️ First request was already cached (video was previously summarized)")
        else:
            logger.info("✅ First request was not cached (as expected)")
        
        # Record the time for the first request
        first_request_time = first_response.elapsed.total_seconds()
        logger.info(f"⏱️ First request time: {first_request_time:.2f} seconds")
        
        # Wait a moment before making the second request
        time.sleep(1)
        
        # Second request - should be cached
        logger.info("Making second request to the same video (should be cached)...")
        second_success, second_response = self.run_test(
            "Second Summarization Request (Cached)",
            "POST",
            "summarize",
            200,
            data={"youtube_url": video_url}
        )
        
        if not second_success:
            logger.error("❌ Second summarization request failed")
            return False, None
        
        second_data = second_response.json()
        second_is_cached = second_data.get('is_cached', False)
        
        # Record the time for the second request
        second_request_time = second_response.elapsed.total_seconds()
        logger.info(f"⏱️ Second request time: {second_request_time:.2f} seconds")
        
        # Verify caching status
        if second_is_cached:
            logger.info("✅ Second request was cached (as expected)")
        else:
            logger.error("❌ Second request was not cached")
            return False, second_response
        
        # Verify response time improvement
        if second_request_time < first_request_time:
            logger.info(f"✅ Cached response was faster: {first_request_time:.2f}s vs {second_request_time:.2f}s")
        else:
            logger.warning(f"⚠️ Cached response was not faster: {first_request_time:.2f}s vs {second_request_time:.2f}s")
        
        # Verify that the content is the same in both responses
        if first_data.get('transcript') == second_data.get('transcript') and \
           first_data.get('summary') == second_data.get('summary'):
            logger.info("✅ Cached response content matches original response")
        else:
            logger.error("❌ Cached response content differs from original response")
            return False, second_response
        
        return True, second_response
        
    def test_recent_videos_api(self):
        """Test that the history API returns recent videos (up to 6)"""
        logger.info("\n🔍 Testing recent videos API...")
        
        success, response = self.run_test(
            "Get Recent Videos",
            "GET",
            "history",
            200
        )
        
        if not success:
            logger.error("❌ Recent videos API request failed")
            return False, None
            
        try:
            history_items = response.json()
            
            # Check if we have history items
            if not history_items:
                logger.warning("⚠️ No history items found, cannot test recent videos feature")
                return False, response
                
            # Check if we have up to 6 recent videos
            recent_videos = history_items[:6]
            logger.info(f"📚 Found {len(recent_videos)} recent videos")
            
            # Verify each recent video has required metadata
            for i, video in enumerate(recent_videos):
                logger.info(f"Checking video {i+1}:")
                
                # Check for video ID
                if 'video_id' in video and video['video_id']:
                    logger.info(f"✅ Video {i+1} has video_id: {video['video_id']}")
                else:
                    logger.error(f"❌ Video {i+1} missing video_id")
                    success = False
                
                # Check for title
                if 'title' in video and video['title']:
                    logger.info(f"✅ Video {i+1} has title: {video['title'][:30]}...")
                else:
                    logger.warning(f"⚠️ Video {i+1} missing title")
                
                # Check for channel
                if 'channel' in video and video['channel']:
                    logger.info(f"✅ Video {i+1} has channel: {video['channel']}")
                else:
                    logger.warning(f"⚠️ Video {i+1} missing channel")
                
                # Check for thumbnail
                if 'thumbnail_url' in video and video['thumbnail_url']:
                    logger.info(f"✅ Video {i+1} has thumbnail")
                else:
                    logger.warning(f"⚠️ Video {i+1} missing thumbnail")
                    
            return success, response
            
        except Exception as e:
            logger.error(f"❌ Error validating recent videos: {str(e)}")
            return False, response

def main():
    print("=" * 80)
    print("🧪 YOUTUBE VIDEO SUMMARIZER API TEST SUITE 🧪")
    print("=" * 80)
    
    tester = YouTubeSummarizerTester()
    
    # Run basic API tests
    api_status_success, _ = tester.test_api_status()
    invalid_url_success, _ = tester.test_invalid_youtube_url()
    
    # Test each video type
    music_video_success, _ = tester.test_valid_youtube_url(tester.music_video_url, "Music")
    comedy_sketch_success, _ = tester.test_valid_youtube_url(tester.comedy_sketch_url, "Comedy Sketch")
    
    # Test caching functionality with the educational video
    caching_success, _ = tester.test_caching_functionality(tester.educational_video_url)
    
    # Test recent videos API
    recent_videos_success, _ = tester.test_recent_videos_api()
    
    # Print results
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 80)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
