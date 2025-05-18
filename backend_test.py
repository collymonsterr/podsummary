
import requests
import sys
import time
from datetime import datetime

class YouTubeSummarizerTester:
    def __init__(self, base_url="https://03994ffd-b1ec-4917-9c69-f797154b536c.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
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
                return success, response.json() if response.status_code != 204 else {}
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
            "API Status Check",
            "GET",
            "",
            200
        )

    def test_summarize_valid_url(self, youtube_url):
        """Test summarizing a valid YouTube URL"""
        return self.run_test(
            "Summarize Valid YouTube URL",
            "POST",
            "summarize",
            200,
            data={"youtube_url": youtube_url}
        )
    
    def test_summarize_invalid_url(self, invalid_url):
        """Test summarizing an invalid YouTube URL"""
        return self.run_test(
            "Summarize Invalid YouTube URL",
            "POST",
            "summarize",
            400,
            data={"youtube_url": invalid_url}
        )
    
    def test_get_history(self):
        """Test getting summary history"""
        return self.run_test(
            "Get Summary History",
            "GET",
            "history",
            200
        )

def main():
    # Setup
    tester = YouTubeSummarizerTester()
    valid_youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    invalid_youtube_url = "https://example.com/not-a-youtube-url"
    
    # Run tests
    api_status_success, _ = tester.test_api_status()
    if not api_status_success:
        print("❌ API status check failed, stopping tests")
        return 1
    
    # Test invalid URL first
    invalid_url_success, _ = tester.test_summarize_invalid_url(invalid_youtube_url)
    
    # Test valid URL
    valid_url_success, response = tester.test_summarize_valid_url(valid_youtube_url)
    if valid_url_success:
        print(f"Video ID: {response.get('video_id')}")
        print(f"Summary length: {len(response.get('summary', ''))}")
        print(f"Transcript length: {len(response.get('transcript', ''))}")
    
    # Test history endpoint
    history_success, history = tester.test_get_history()
    if history_success:
        print(f"History items: {len(history)}")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
