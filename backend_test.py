
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
    
    def validate_transcript_and_summary(self, response):
        """Validate that transcript and summary are properly generated"""
        print("\n🔍 Validating transcript and summary content...")
        
        transcript = response.get('transcript', '')
        summary = response.get('summary', '')
        video_id = response.get('video_id', '')
        url = response.get('url', '')
        
        validation_results = []
        
        # Check if transcript is not empty
        if transcript:
            print("✅ Transcript is not empty")
            validation_results.append(True)
        else:
            print("❌ Transcript is empty")
            validation_results.append(False)
        
        # Check if summary is not empty
        if summary:
            print("✅ Summary is not empty")
            validation_results.append(True)
        else:
            print("❌ Summary is empty")
            validation_results.append(False)
        
        # Check if video_id is valid
        if video_id and len(video_id) == 11:
            print(f"✅ Valid video ID: {video_id}")
            validation_results.append(True)
        else:
            print(f"❌ Invalid video ID: {video_id}")
            validation_results.append(False)
        
        # Check if URL is valid
        if url and ('youtube.com' in url or 'youtu.be' in url):
            print(f"✅ Valid URL: {url}")
            validation_results.append(True)
        else:
            print(f"❌ Invalid URL: {url}")
            validation_results.append(False)
        
        # Check if summary is shorter than transcript (as expected)
        if len(summary) < len(transcript):
            print("✅ Summary is shorter than transcript (as expected)")
            validation_results.append(True)
        else:
            print("❌ Summary is not shorter than transcript")
            validation_results.append(False)
        
        # Print content lengths
        print(f"📏 Transcript length: {len(transcript)} characters")
        print(f"📏 Summary length: {len(summary)} characters")
        
        # Return True if all validations passed
        all_passed = all(validation_results)
        if all_passed:
            self.tests_passed += 1
        self.tests_run += 1
        
        return all_passed

def main():
    # Setup
    tester = YouTubeSummarizerTester()
    valid_youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    invalid_youtube_url = "https://example.com/not-a-youtube-url"
    
    print("=" * 80)
    print("🧪 YOUTUBE VIDEO SUMMARIZER API TEST SUITE 🧪")
    print("=" * 80)
    
    # Run tests
    api_status_success, _ = tester.test_api_status()
    if not api_status_success:
        print("❌ API status check failed, stopping tests")
        return 1
    
    # Test invalid URL first
    invalid_url_success, _ = tester.test_summarize_invalid_url(invalid_youtube_url)
    
    # Test valid URL
    print("\n⏳ Testing video summarization (this may take a minute)...")
    valid_url_success, response = tester.test_summarize_valid_url(valid_youtube_url)
    
    if valid_url_success:
        # Validate the content of the response
        content_valid = tester.validate_transcript_and_summary(response)
        if not content_valid:
            print("⚠️ Response content validation failed")
    
    # Test history endpoint
    history_success, history = tester.test_get_history()
    if history_success:
        print(f"📚 History items: {len(history)}")
        if len(history) > 0:
            print(f"📅 Most recent summary: {history[0]['url']} ({history[0]['video_id']})")
    
    # Print results
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 80)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
