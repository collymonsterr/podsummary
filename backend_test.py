import requests
import sys
import os
import time

class YouTubeSummarizerTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_key = "yt-summarizer-admin-2025"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # A well-known video that's unlikely to be removed

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
                return True, response.json() if response.text else {}
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

    def test_summarize_video(self):
        """Test video summarization"""
        success, response = self.run_test(
            "Summarize Video",
            "POST",
            "summarize",
            200,
            data={"youtube_url": self.test_video_url}
        )
        return success, response

    def test_get_history(self):
        """Test getting video history"""
        return self.run_test("Get History", "GET", "history", 200)

    def test_delete_transcript(self, transcript_id):
        """Test deleting a transcript with admin key"""
        headers = {
            'Content-Type': 'application/json',
            'admin-key': self.admin_key
        }
        return self.run_test(
            "Delete Transcript",
            "DELETE",
            f"admin/transcript/{transcript_id}",
            200,
            headers=headers
        )

    def test_delete_transcript_invalid_key(self, transcript_id):
        """Test deleting a transcript with invalid admin key"""
        headers = {
            'Content-Type': 'application/json',
            'admin-key': 'invalid-key'
        }
        success, _ = self.run_test(
            "Delete Transcript with Invalid Key",
            "DELETE",
            f"admin/transcript/{transcript_id}",
            403,
            headers=headers
        )
        return success

def main():
    # Get backend URL from environment variable or use default
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://03994ffd-b1ec-4917-9c69-f797154b536c.preview.emergentagent.com')
    
    print(f"Testing YouTube Summarizer API at: {backend_url}")
    tester = YouTubeSummarizerTester(backend_url)

    # Test API status
    api_status_success, _ = tester.test_api_status()
    if not api_status_success:
        print("❌ API status check failed, stopping tests")
        return 1

    # Test getting history
    history_success, history_data = tester.test_get_history()
    if not history_success:
        print("❌ History retrieval failed, stopping tests")
        return 1
    
    print(f"Found {len(history_data)} videos in history")
    
    # Test video summarization if needed
    if not history_data:
        print("No videos in history, testing summarization...")
        summarize_success, summarize_data = tester.test_summarize_video()
        if not summarize_success:
            print("❌ Video summarization failed")
            return 1
        
        # Get updated history after summarization
        _, history_data = tester.test_get_history()
    
    # Test transcript deletion with invalid key
    if history_data:
        transcript_id = history_data[0]['id']
        print(f"Testing deletion with invalid key for transcript ID: {transcript_id}")
        invalid_key_success = tester.test_delete_transcript_invalid_key(transcript_id)
        if not invalid_key_success:
            print("❌ Invalid key test failed")
    
    # Test transcript deletion with valid key
    if history_data:
        transcript_id = history_data[0]['id']
        print(f"Testing deletion with valid key for transcript ID: {transcript_id}")
        delete_success, _ = tester.test_delete_transcript(transcript_id)
        
        if delete_success:
            # Verify deletion by checking history again
            _, updated_history = tester.test_get_history()
            deleted = all(item['id'] != transcript_id for item in updated_history)
            
            if deleted:
                print("✅ Transcript successfully deleted and removed from history")
                tester.tests_passed += 1
            else:
                print("❌ Transcript still exists in history after deletion")
                tester.tests_run += 1
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
