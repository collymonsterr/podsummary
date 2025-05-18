import requests
import sys
import time
from datetime import datetime

class PodBriefAPITester:
    def __init__(self, base_url="https://03994ffd-b1ec-4917-9c69-f797154b536c.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return success, response.json() if response.text else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_status(self):
        """Test API root endpoint"""
        return self.run_test(
            "API Status",
            "GET",
            "",
            200
        )

    def test_summarize_video(self, youtube_url):
        """Test video summarization"""
        success, response = self.run_test(
            "Video Summarization",
            "POST",
            "summarize",
            200,
            data={"youtube_url": youtube_url}
        )
        return success, response

    def test_get_history(self):
        """Test getting history of summarized videos"""
        return self.run_test(
            "Get History",
            "GET",
            "history",
            200
        )

    def test_channel_videos(self, channel_url):
        """Test getting videos from a channel"""
        success, response = self.run_test(
            "Channel Videos",
            "POST",
            "channel-videos",
            200,
            data={"channel_url": channel_url}
        )
        return success, response

def main():
    # Setup
    tester = PodBriefAPITester()
    
    # Test API status
    api_status, _ = tester.test_api_status()
    if not api_status:
        print("❌ API status check failed, stopping tests")
        return 1

    # Test video summarization
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    summary_success, summary_response = tester.test_summarize_video(test_video_url)
    
    if summary_success:
        print(f"Video ID: {summary_response.get('video_id')}")
        print(f"Title: {summary_response.get('title')}")
        print(f"Channel: {summary_response.get('channel')}")
        print(f"Summary length: {len(summary_response.get('summary', ''))}")
        print(f"Transcript length: {len(summary_response.get('transcript', ''))}")
    else:
        print("❌ Video summarization failed")

    # Test history endpoint
    history_success, history_response = tester.test_get_history()
    if history_success:
        print(f"History items: {len(history_response)}")
    else:
        print("❌ History retrieval failed")

    # Test channel videos endpoint
    channel_url = "https://www.youtube.com/@hubermanlab"
    channel_success, channel_response = tester.test_channel_videos(channel_url)
    if channel_success:
        print(f"Channel name: {channel_response.get('channel_name')}")
        print(f"Videos found: {len(channel_response.get('videos', []))}")
    else:
        print("❌ Channel videos retrieval failed")

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
