
import requests
import sys
import time
import os
from datetime import datetime

class PodBriefAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.admin_key = "yt-summarizer-admin-2025"  # From backend/.env
        self.tests_run = 0
        self.tests_passed = 0
        self.test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # A well-known video that should work

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
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
                if response.text:
                    try:
                        return success, response.json()
                    except:
                        return success, response.text
                return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test the API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        if success:
            print(f"API Message: {response.get('message', '')}")
        return success

    def test_summarize_video(self):
        """Test the summarize endpoint with a YouTube URL"""
        success, response = self.run_test(
            "Summarize Video",
            "POST",
            "summarize",
            200,
            data={"youtube_url": self.test_video_url}
        )
        
        if success:
            # Verify the response contains expected fields
            required_fields = ["transcript", "summary", "video_id", "url"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Response missing required fields: {', '.join(missing_fields)}")
                return False
                
            print(f"✅ Successfully summarized video. Video ID: {response.get('video_id')}")
            print(f"✅ Title: {response.get('title')}")
            print(f"✅ Channel: {response.get('channel')}")
            print(f"✅ Summary length: {len(response.get('summary', ''))}")
            print(f"✅ Transcript length: {len(response.get('transcript', ''))}")
            
            # Store video ID for potential deletion test
            self.test_video_id = response.get('id')
            return True
        return False

    def test_get_history(self):
        """Test the history endpoint"""
        success, response = self.run_test(
            "Get History",
            "GET",
            "history",
            200
        )
        
        if success and isinstance(response, list):
            print(f"✅ Retrieved {len(response)} history items")
            
            # If we have history items, store the first ID for deletion test
            if response and len(response) > 0:
                self.history_item_id = response[0].get('id')
                print(f"✅ First history item ID: {self.history_item_id}")
                print(f"✅ First history item title: {response[0].get('title')}")
            return True
        return False

    def test_channel_videos(self):
        """Test the channel-videos endpoint"""
        channel_url = "https://www.youtube.com/@hubermanlab"
        success, response = self.run_test(
            "Get Channel Videos",
            "POST",
            "channel-videos",
            200,
            data={"channel_url": channel_url}
        )
        
        if success:
            if "channel_name" in response and "videos" in response:
                print(f"✅ Channel name: {response['channel_name']}")
                print(f"✅ Retrieved {len(response['videos'])} videos")
                
                # Check if we have the expected number of videos (should be 6 based on server.py)
                if len(response['videos']) == 6:
                    print("✅ Correct number of videos returned (6)")
                else:
                    print(f"⚠️ Expected 6 videos, got {len(response['videos'])}")
                
                # Check if videos have required fields
                if response['videos']:
                    first_video = response['videos'][0]
                    required_fields = ["id", "title", "link", "thumbnail"]
                    missing_fields = [field for field in required_fields if field not in first_video]
                    
                    if missing_fields:
                        print(f"❌ Video missing required fields: {', '.join(missing_fields)}")
                        return False
                    
                    print(f"✅ First video title: {first_video['title']}")
                return True
            else:
                print("❌ Response missing 'channel_name' or 'videos' fields")
                return False
        return False

    def test_admin_delete(self):
        """Test the admin delete endpoint"""
        if not hasattr(self, 'history_item_id'):
            print("⚠️ No history item ID available for deletion test")
            return False
            
        headers = {
            'Content-Type': 'application/json',
            'admin-key': self.admin_key
        }
        
        success, response = self.run_test(
            "Admin Delete Transcript",
            "DELETE",
            f"admin/transcript/{self.history_item_id}",
            200,
            headers=headers
        )
        
        if success:
            print(f"✅ Successfully deleted transcript with ID: {self.history_item_id}")
            return True
        return False

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://03994ffd-b1ec-4917-9c69-f797154b536c.preview.emergentagent.com"
    
    print(f"🚀 Starting PodBrief API tests against {backend_url}")
    
    # Setup tester
    tester = PodBriefAPITester(backend_url)
    
    # Run tests
    api_root_success = tester.test_api_root()
    if not api_root_success:
        print("❌ API root test failed, stopping tests")
        return 1
        
    history_success = tester.test_get_history()
    if not history_success:
        print("❌ History test failed")
    
    channel_success = tester.test_channel_videos()
    if not channel_success:
        print("❌ Channel videos test failed")
        
    summarize_success = tester.test_summarize_video()
    if not summarize_success:
        print("❌ Summarize test failed")
    
    # Only run delete test if we have a history item
    if hasattr(tester, 'history_item_id'):
        delete_success = tester.test_admin_delete()
        if not delete_success:
            print("❌ Admin delete test failed")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
