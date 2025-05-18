
import requests
import time
import sys
import json
from datetime import datetime

class YouTubeSummarizerTester:
    def __init__(self, base_url="https://03994ffd-b1ec-4917-9c69-f797154b536c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_key = "yt-summarizer-admin-2025"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_videos = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo - first YouTube video
            "https://www.youtube.com/watch?v=_vS_b7cJn2A"    # TED Talk
        ]

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if not headers:
            headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
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
                print(f"✅ Passed - Status: {response.status_code}")
                return success, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_status(self):
        """Test API status endpoint"""
        return self.run_test("API Status", "GET", "", 200)

    def test_summarize_video(self, youtube_url):
        """Test video summarization"""
        start_time = time.time()
        success, response = self.run_test(
            f"Summarize Video ({youtube_url})",
            "POST",
            "summarize",
            200,
            data={"youtube_url": youtube_url}
        )
        end_time = time.time()
        processing_time = end_time - start_time
        
        if success:
            print(f"Processing time: {processing_time:.2f} seconds")
            print(f"Video ID: {response.get('video_id', 'N/A')}")
            print(f"Title: {response.get('title', 'N/A')}")
            print(f"Channel: {response.get('channel', 'N/A')}")
            print(f"Cached: {response.get('is_cached', False)}")
            print(f"Transcript length: {len(response.get('transcript', ''))}")
            print(f"Summary length: {len(response.get('summary', ''))}")
            
            # Verify we have all required fields
            required_fields = ['transcript', 'summary', 'video_id', 'url']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Missing required fields: {', '.join(missing_fields)}")
                return False, response, processing_time
                
            return True, response, processing_time
        
        return False, {}, processing_time

    def test_caching(self, youtube_url):
        """Test caching functionality by requesting the same video twice"""
        print(f"\n🔍 Testing caching for {youtube_url}...")
        
        # First request
        print("First request (should not be cached):")
        success1, response1, time1 = self.test_summarize_video(youtube_url)
        
        if not success1:
            print("❌ First request failed, cannot test caching")
            return False
            
        # Second request (should be cached)
        print("\nSecond request (should be cached):")
        success2, response2, time2 = self.test_summarize_video(youtube_url)
        
        if not success2:
            print("❌ Second request failed")
            return False
            
        # Verify it's cached
        if not response2.get('is_cached', False):
            print("❌ Response not marked as cached")
            return False
            
        # Verify faster response time
        if time2 >= time1:
            print(f"❌ Cached response not faster: {time2:.2f}s vs {time1:.2f}s")
            return False
            
        # Verify same content
        if response1.get('transcript') != response2.get('transcript'):
            print("❌ Transcripts don't match between requests")
            return False
            
        if response1.get('summary') != response2.get('summary'):
            print("❌ Summaries don't match between requests")
            return False
            
        print(f"✅ Caching test passed! First request: {time1:.2f}s, Second request: {time2:.2f}s")
        print(f"✅ Speed improvement: {(time1-time2)/time1*100:.1f}%")
        return True

    def test_history(self):
        """Test history endpoint"""
        success, response = self.run_test("Get History", "GET", "history", 200)
        
        if success:
            print(f"Number of history items: {len(response)}")
            
            if len(response) > 0:
                # Check first item has required fields
                first_item = response[0]
                required_fields = ['id', 'video_id', 'url', 'transcript', 'summary', 'timestamp']
                missing_fields = [field for field in required_fields if field not in first_item]
                
                if missing_fields:
                    print(f"❌ History item missing required fields: {', '.join(missing_fields)}")
                    return False
                    
                # Check for metadata fields
                metadata_fields = ['title', 'channel', 'thumbnail_url']
                has_metadata = all(field in first_item for field in metadata_fields)
                
                if not has_metadata:
                    print("⚠️ History item missing some metadata fields")
                
                return True
            else:
                print("⚠️ History is empty, cannot fully validate")
                return True
        
        return False

    def test_delete_transcript_with_valid_admin_key(self, transcript_id):
        """Test deleting a transcript with valid admin key"""
        headers = {
            'Content-Type': 'application/json',
            'admin-key': self.admin_key
        }
        return self.run_test(
            "Delete Transcript with Valid Admin Key",
            "DELETE",
            f"admin/transcript/{transcript_id}",
            200,
            headers=headers
        )

    def test_delete_transcript_with_invalid_admin_key(self, transcript_id):
        """Test deleting a transcript with invalid admin key"""
        headers = {
            'Content-Type': 'application/json',
            'admin-key': 'invalid-key'
        }
        return self.run_test(
            "Delete Transcript with Invalid Admin Key",
            "DELETE",
            f"admin/transcript/{transcript_id}",
            403,
            headers=headers
        )

    def test_delete_transcript_without_admin_key(self, transcript_id):
        """Test deleting a transcript without admin key"""
        return self.run_test(
            "Delete Transcript without Admin Key",
            "DELETE",
            f"admin/transcript/{transcript_id}",
            403
        )

def main():
    print("=" * 60)
    print("YouTube Video Summarizer API Test")
    print("=" * 60)
    
    tester = YouTubeSummarizerTester()
    
    # Test 1: API Status
    api_status, _ = tester.test_api_status()
    if not api_status:
        print("❌ API is not responding, stopping tests")
        return 1
        
    # Test 2: Summarize a video
    print("\n" + "=" * 60)
    print("Testing Summary Caching Feature")
    print("=" * 60)
    
    # Test with music video
    caching_success = tester.test_caching(tester.test_videos[0])
    
    # Test 3: Get history
    print("\n" + "=" * 60)
    print("Testing History Feature")
    print("=" * 60)
    history_success, history_data = tester.test_history()
    
    # Test 4: Summarize multiple videos to populate recent videos
    print("\n" + "=" * 60)
    print("Testing Multiple Video Summaries")
    print("=" * 60)
    
    for i, video_url in enumerate(tester.test_videos[1:], 1):
        print(f"\nTesting video {i+1} of {len(tester.test_videos)}: {video_url}")
        success, _, _ = tester.test_summarize_video(video_url)
        if not success:
            print(f"❌ Failed to summarize video {i+1}")
    
    # Test 5: Admin functionality
    print("\n" + "=" * 60)
    print("Testing Admin Functionality")
    print("=" * 60)
    
    # Get the first video ID for deletion tests
    if history_success and history_data and len(history_data) > 0:
        transcript_id = history_data[0]['id']
        print(f"Using transcript ID for testing: {transcript_id}")
        
        # Test deletion without admin key
        tester.test_delete_transcript_without_admin_key(transcript_id)
        
        # Test deletion with invalid admin key
        tester.test_delete_transcript_with_invalid_admin_key(transcript_id)
        
        # Test deletion with valid admin key
        # Note: This will actually delete the transcript, so it's the last test
        tester.test_delete_transcript_with_valid_admin_key(transcript_id)
    else:
        print("⚠️ No videos in history to test admin deletion functionality")
    
    # Print results
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if not caching_success:
        print("❌ Caching feature test failed")
    else:
        print("✅ Caching feature test passed")
        
    if not history_success:
        print("❌ History feature test failed")
    else:
        print("✅ History feature test passed")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
