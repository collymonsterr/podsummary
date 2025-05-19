import requests
import sys
import time
from datetime import datetime

class PodBriefAPITester:
    def __init__(self, base_url="https://2741a2ce-05d6-4231-a8fb-a5540c0f1367.preview.emergentagent.com/api"):
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

    # Test "Just Have a Think" channel videos
    justhaveathink_url = "https://www.youtube.com/@JustHaveaThink"
    justhaveathink_success, justhaveathink_response = tester.test_channel_videos(justhaveathink_url)
    
    if justhaveathink_success:
        print(f"Channel name: {justhaveathink_response.get('channel_name')}")
        videos = justhaveathink_response.get('videos', [])
        print(f"Videos found: {len(videos)}")
        
        # Verify we have exactly 6 videos for Just Have a Think
        if len(videos) == 6:
            print("✅ Correct number of videos (6) returned for Just Have a Think")
            
            # Check if all videos are from the correct channel
            all_correct_channel = all(video.get('channel', {}).get('name') == "Just Have A Think" for video in videos)
            if all_correct_channel:
                print("✅ All videos are from the correct channel")
            else:
                print("❌ Some videos are not from the correct channel")
                
            # Print video titles for verification
            print("\nJust Have a Think videos:")
            for i, video in enumerate(videos):
                print(f"{i+1}. {video.get('title')}")
        else:
            print(f"❌ Expected 6 videos, got {len(videos)}")
    else:
        print("❌ Just Have a Think channel videos retrieval failed")

    # Test Huberman Lab channel videos
    huberman_url = "https://www.youtube.com/@hubermanlab"
    huberman_success, huberman_response = tester.test_channel_videos(huberman_url)
    
    if huberman_success:
        print(f"\nChannel name: {huberman_response.get('channel_name')}")
        videos = huberman_response.get('videos', [])
        print(f"Videos found: {len(videos)}")
        
        # Print video titles for verification
        print("\nHuberman Lab videos:")
        for i, video in enumerate(videos):
            print(f"{i+1}. {video.get('title')}")
    else:
        print("❌ Huberman Lab channel videos retrieval failed")

    # Test Lex Fridman channel videos
    lex_url = "https://www.youtube.com/@lexfridman"
    lex_success, lex_response = tester.test_channel_videos(lex_url)
    
    if lex_success:
        print(f"\nChannel name: {lex_response.get('channel_name')}")
        videos = lex_response.get('videos', [])
        print(f"Videos found: {len(videos)}")
        
        # Print video titles for verification
        print("\nLex Fridman videos:")
        for i, video in enumerate(videos):
            print(f"{i+1}. {video.get('title')}")
    else:
        print("❌ Lex Fridman channel videos retrieval failed")

    # Test video summarization for one of the Just Have a Think videos
    if justhaveathink_success and len(justhaveathink_response.get('videos', [])) > 0:
        test_video = justhaveathink_response['videos'][0]
        test_video_url = test_video.get('link')
        print(f"\nTesting summarization for video: {test_video.get('title')}")
        
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
        print(f"\nHistory items: {len(history_response)}")
    else:
        print("❌ History retrieval failed")

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
