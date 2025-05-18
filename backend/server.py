from fastapi import FastAPI, APIRouter, HTTPException, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import requests
import openai
import re
import nltk

# Download NLTK data at startup
try:
    nltk.download('punkt')
except Exception as e:
    logging.warning(f"Failed to download NLTK data: {str(e)}")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure API keys
searchapi_key = os.environ.get('SEARCHAPI_KEY')
openai_api_key = os.environ.get('OPENAI_API_KEY')
openai.api_key = openai_api_key

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class VideoRequest(BaseModel):
    youtube_url: str

class TranscriptResponse(BaseModel):
    transcript: str
    summary: str
    video_id: str
    url: str
    title: Optional[str] = None
    channel: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_cached: bool = False

class StoredTranscript(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    url: str
    transcript: str
    summary: str
    title: Optional[str] = None
    channel: Optional[str] = None
    thumbnail_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Extract YouTube video ID from various YouTube URL formats
def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    raise ValueError("Could not extract video ID from URL")

# Extract YouTube video metadata using alternate methods when SearchAPI is unavailable
async def get_video_metadata(video_id):
    # First try SearchAPI
    try:
        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "engine": "youtube",
            "api_key": searchapi_key,
            "q": f"https://www.youtube.com/watch?v={video_id}"
        }
        
        logging.info(f"Fetching metadata for video ID: {video_id}")
        response = requests.get(url, params=params)
        
        if response.status_code == 200 and 'video_results' in response.json() and response.json()['video_results']:
            data = response.json()
            video = data['video_results'][0]
            
            title = video.get('title', '')
            channel = video.get('channel', {}).get('name', '')
            thumbnail_url = video.get('thumbnail', {}).get('static', '')
            
            logging.info(f"Retrieved metadata from SearchAPI for '{title}' by {channel}")
            return title, channel, thumbnail_url
    except Exception as e:
        logging.warning(f"Error using SearchAPI for metadata: {str(e)}")
    
    # Fallback to YouTube API iframe data
    try:
        # This uses YouTube's oEmbed API which doesn't require API key
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url)
        
        if response.status_code == 200:
            data = response.json()
            title = data.get('title', '')
            channel = data.get('author_name', '')
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"  # Use high quality thumbnail
            
            logging.info(f"Retrieved metadata from YouTube oEmbed API for '{title}' by {channel}")
            return title, channel, thumbnail_url
    except Exception as e:
        logging.warning(f"Error using YouTube oEmbed API for metadata: {str(e)}")
    
    # Ultimate fallback: use video ID as title and default values
    logging.warning(f"Using fallback metadata for video ID: {video_id}")
    return f"YouTube Video ({video_id})", "YouTube Channel", f"https://img.youtube.com/vi/{video_id}/0.jpg"

# Get transcript using SearchAPI.io
async def get_transcript(video_id):
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "youtube_transcripts",
        "api_key": searchapi_key,
        "video_id": video_id,
        "lang": "en"
    }
    
    logging.info(f"Requesting transcript for video ID: {video_id}")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        error_msg = f"Failed to get transcript: {response.text}"
        logging.error(error_msg)
        raise HTTPException(
            status_code=response.status_code,
            detail=error_msg
        )
        
    data = response.json()
    
    if 'transcripts' not in data or not data['transcripts']:
        error_msg = "No transcript found for this video"
        logging.error(f"{error_msg} (video ID: {video_id})")
        raise HTTPException(
            status_code=400,
            detail=error_msg
        )
    
    # Extract text from transcript segments and join with spaces
    # Process segments in order of start time to ensure proper sequence
    segments = sorted(data['transcripts'], key=lambda x: x.get('start', 0))
    
    # Extract the text and clean it
    transcript_parts = []
    for segment in segments:
        text = segment.get('text', '').strip()
        if text:
            transcript_parts.append(text)
    
    # Join all parts with spaces
    full_transcript = " ".join(transcript_parts)
    
    # Log the length of the transcript for debugging
    logging.info(f"Retrieved transcript with {len(full_transcript)} characters and {len(segments)} segments")
    
    return full_transcript

# Summarize text using OpenAI's API or a fallback method
async def summarize_text(text):
    try:
        # If transcript is very long, truncate it to avoid excessive token usage
        max_chars = 16000  # Approximate char count that fits in context
        if len(text) > max_chars:
            logging.info(f"Truncating transcript from {len(text)} to {max_chars} characters")
            text = text[:max_chars]
            
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Most cost-effective model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates clear, concise summaries of YouTube video transcripts. Use appropriate emojis to make your summaries more engaging and visually appealing."},
                {"role": "user", "content": f"Summarise this video transcript clearly and concisely. List the main topics discussed in the order they appear, and highlight the most interesting or surprising insights. Use appropriate emojis before each main point and insight to make the summary more engaging. Write it so someone can quickly decide if it's worth watching the full video.\n\nTranscript:\n{text}"}
            ],
            temperature=0.5,
            max_tokens=500  # Reduced from 1000 to save on tokens
        )
        
        summary = response.choices[0].message.content
        logging.info(f"Successfully generated OpenAI summary of length {len(summary)}")
        return summary
    except Exception as openai_error:
        logging.error(f"OpenAI API error: {str(openai_error)}")
        
        # Special handling for song lyrics
        if "♪" in text:
            return "🎵 This appears to be a song with lyrics. Here are the main lyrics: 🎵\n\n" + summarize_song_lyrics(text)
        
        # Simple extractive summarization fallback that will always work
        logging.info("Using basic fallback summarization method")
        try:
            # Split text into chunks - use a simple period split if it's a song lyrics or similar
            chunks = text.split('. ')
            
            # For very short text, just return it
            if len(text) < 500 or len(chunks) < 5:
                return "📝 The transcript is too short to summarize effectively. Here it is in full:\n\n" + text
                
            # Create a simple extractive summary with proper formatting to match requested style
            summary = "# 📋 Summary of Video Transcript\n\n## 🔍 Main Topics Discussed\n\n"
            
            # Emojis for different topics
            topic_emojis = ["🔸", "🔹", "💡", "📌", "🔆", "✨", "📣", "🔍", "📈", "🌟"]
            
            # Extract topics from chunks
            topics = []
            
            # Always take the first chunk (often contains title or intro)
            if chunks[0]:
                topics.append(f"1. {topic_emojis[0]} Introduction: " + chunks[0].strip())
                
            # Take samples throughout the text for main points
            if len(chunks) > 10:
                # For longer texts, take samples at regular intervals
                sample_interval = max(1, len(chunks) // 5)
                for i in range(1, 5):  # Get about 4-5 main points
                    idx = min(i * sample_interval, len(chunks) - 1)
                    if chunks[idx].strip():
                        emoji_idx = min(i, len(topic_emojis) - 1)
                        topics.append(f"{i+1}. {topic_emojis[emoji_idx]} {chunks[idx].strip()}")
            else:
                # For shorter texts, take every other chunk
                for i in range(1, min(5, len(chunks))):
                    if chunks[i].strip():
                        emoji_idx = min(i, len(topic_emojis) - 1)
                        topics.append(f"{i+1}. {topic_emojis[emoji_idx]} {chunks[i].strip()}")
            
            # Add the topics to the summary
            summary += "\n".join(topics)
            
            # Add insights section
            summary += "\n\n## 💎 Key Insights\n\n"
            
            # Take last chunk as conclusion or insight if available
            if chunks[-1] and chunks[-1] not in topics:
                summary += "* 🔑 " + chunks[-1].strip() + "\n"
            
            # Add a sample from middle of video as another insight
            mid_idx = len(chunks) // 2
            if chunks[mid_idx] and chunks[mid_idx] not in topics:
                summary += "* 💫 " + chunks[mid_idx].strip() + "\n"
            
            # Add disclaimer about the fallback method
            summary += "\n\n*⚠️ Note: This is an automatic summary created without AI due to API limits. For best results, try again later.*"
            
            return summary
            
        except Exception as fallback_error:
            logging.error(f"Error in fallback summarization: {str(fallback_error)}")
            # Ultimate fallback - return a message that still allows the user to see the transcript
            return "❗ Sorry, we couldn't generate a summary for this video. Please check the transcript tab to see the full text."

def summarize_song_lyrics(text):
    """Special function to summarize song lyrics"""
    lines = text.split("\n")
    
    # Filter out music notes and empty lines
    lyrics = [line.strip() for line in lines if line.strip() and "♪" not in line]
    
    # Remove duplicates (common in songs with chorus)
    unique_lyrics = []
    for line in lyrics:
        if line not in unique_lyrics:
            unique_lyrics.append(line)
    
    # If we have very few unique lines, return them all
    if len(unique_lyrics) < 8:
        return "🎤 " + "\n🎵 ".join(unique_lyrics)
    
    # Otherwise, take representative samples
    summary = []
    
    # Always include first line if available
    if unique_lyrics and len(unique_lyrics) > 0:
        summary.append("🎤 " + unique_lyrics[0])
    
    # Take samples at regular intervals
    if len(unique_lyrics) > 5:
        interval = max(1, len(unique_lyrics) // 5)
        for i in range(interval, len(unique_lyrics), interval):
            summary.append("🎵 " + unique_lyrics[i])
    
    # Always include last line if not already included
    if unique_lyrics and unique_lyrics[-1] not in summary:
        summary.append("🎶 " + unique_lyrics[-1])
    
    return "\n".join(summary)

# Route to get transcript and summary from YouTube URL
@api_router.post("/summarize", response_model=TranscriptResponse)
async def summarize_youtube_video(request: VideoRequest):
    try:
        # Extract YouTube video ID from URL
        try:
            video_id = extract_video_id(request.youtube_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Check if we already have this video's data in our database
        existing = await db.transcripts.find_one({"video_id": video_id})
        
        title = None
        channel = None 
        thumbnail_url = None
        transcript = ""
        is_cached = False
        
        # If we have a complete cached result, return it immediately
        if existing and "transcript" in existing and "summary" in existing:
            logging.info(f"Found cached result for video ID: {video_id}")
            title = existing.get("title")
            channel = existing.get("channel")
            thumbnail_url = existing.get("thumbnail_url")
            
            # If we have transcript and summary but no metadata, try to fetch it
            if not title or not channel or not thumbnail_url:
                try:
                    title, channel, thumbnail_url = await get_video_metadata(video_id)
                    
                    # Update the existing record with metadata
                    if title and channel:
                        await db.transcripts.update_one(
                            {"_id": existing["_id"]},
                            {"$set": {
                                "title": title,
                                "channel": channel,
                                "thumbnail_url": thumbnail_url
                            }}
                        )
                except Exception as e:
                    logging.error(f"Error updating metadata: {str(e)}")
            
            # Return cached result
            return TranscriptResponse(
                transcript=existing["transcript"],
                summary=existing["summary"],
                video_id=existing["video_id"],
                url=existing["url"],
                title=title,
                channel=channel,
                thumbnail_url=thumbnail_url,
                is_cached=True
            )
        
        # We need to get the transcript
        if existing and "transcript" in existing and existing["transcript"]:
            # Use the cached transcript
            transcript = existing["transcript"]
            is_cached = True
            logging.info(f"Using cached transcript for video ID: {video_id}")
        else:
            # Get transcript from YouTube
            try:
                transcript = await get_transcript(video_id)
                logging.info(f"Retrieved new transcript for video ID: {video_id}")
            except Exception as e:
                logging.error(f"Error getting transcript: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Fetch video metadata if we don't have it
        if not title or not channel or not thumbnail_url:
            try:
                title, channel, thumbnail_url = await get_video_metadata(video_id)
            except Exception as e:
                logging.error(f"Error fetching metadata: {str(e)}")
        
        # Generate a summary
        summary = await summarize_text(transcript)
        logging.info(f"Generated new summary for video ID: {video_id}")
        
        # Store or update in database
        if existing:
            # Update the existing record with new data
            update_data = {
                "summary": summary,
                "timestamp": datetime.utcnow()
            }
            
            # Add metadata if available
            if title:
                update_data["title"] = title
            if channel:
                update_data["channel"] = channel
            if thumbnail_url:
                update_data["thumbnail_url"] = thumbnail_url
            
            await db.transcripts.update_one(
                {"_id": existing["_id"]},
                {"$set": update_data}
            )
        else:
            # Create a new record
            transcript_obj = StoredTranscript(
                video_id=video_id,
                url=request.youtube_url,
                transcript=transcript,
                summary=summary,
                title=title,
                channel=channel,
                thumbnail_url=thumbnail_url
            )
            await db.transcripts.insert_one(transcript_obj.dict())
        
        return TranscriptResponse(
            transcript=transcript,
            summary=summary,
            video_id=video_id,
            url=request.youtube_url,
            title=title,
            channel=channel,
            thumbnail_url=thumbnail_url,
            is_cached=is_cached
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(f"Unexpected error in summarize_youtube_video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Get history of previously summarized videos
@api_router.get("/history", response_model=List[StoredTranscript])
async def get_summary_history():
    history = await db.transcripts.find().sort("timestamp", -1).to_list(20)
    
    # Process results to add any missing metadata for videos
    for item in history:
        # If we're missing metadata, try to fetch it
        if (not item.get("title") or not item.get("channel") or not item.get("thumbnail_url")) and "video_id" in item:
            try:
                title, channel, thumbnail_url = await get_video_metadata(item["video_id"])
                
                # Update the record if we got metadata
                if title and channel:
                    await db.transcripts.update_one(
                        {"_id": item["_id"]},
                        {"$set": {
                            "title": title,
                            "channel": channel,
                            "thumbnail_url": thumbnail_url
                        }}
                    )
                    
                    # Update the item in our results
                    item["title"] = title
                    item["channel"] = channel
                    item["thumbnail_url"] = thumbnail_url
            except Exception as e:
                logging.error(f"Error fetching metadata for history item: {str(e)}")
    
    return [StoredTranscript(**item) for item in history]

# Update metadata for existing videos without metadata
@api_router.post("/update-metadata", response_model=dict)
async def update_video_metadata():
    # Find all videos without metadata
    videos_without_metadata = await db.transcripts.find({
        "$or": [
            {"title": None},
            {"channel": None},
            {"thumbnail_url": None},
            {"title": {"$exists": False}},
            {"channel": {"$exists": False}},
            {"thumbnail_url": {"$exists": False}}
        ]
    }).to_list(100)
    
    updated_count = 0
    
    # Update each video
    for video in videos_without_metadata:
        if "video_id" in video:
            try:
                title, channel, thumbnail_url = await get_video_metadata(video["video_id"])
                
                if title and channel:
                    # Update the database entry
                    await db.transcripts.update_one(
                        {"_id": video["_id"]},
                        {"$set": {
                            "title": title,
                            "channel": channel,
                            "thumbnail_url": thumbnail_url
                        }}
                    )
                    updated_count += 1
            except Exception as e:
                logging.error(f"Error updating metadata for video {video['video_id']}: {str(e)}")
    
    return {"updated_videos": updated_count, "total_processed": len(videos_without_metadata)}

# Get channel videos from YouTube
@api_router.post("/channel-videos", response_model=dict)
async def get_channel_videos(request: dict):
    channel_url = request.get("channel_url")
    if not channel_url:
        raise HTTPException(status_code=400, detail="Channel URL is required")
    
    try:
        # Use SearchAPI.io to get latest videos from channel
        response = requests.get(
            "https://www.searchapi.io/api/v1/search",
            params={
                "engine": "youtube",
                "q": f"channel:{channel_url} videos",
                "api_key": searchapi_key
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch channel videos: {response.text}")
        
        data = response.json()
        videos = data.get("video_results", [])[:6]  # Get most recent 6
        
        return {
            "channel_name": videos[0].get("channel", {}).get("name") if videos else "",
            "videos": videos
        }
    except Exception as e:
        logging.error(f"Error fetching channel videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Podbrief API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Admin endpoint for deleting a transcript
@api_router.delete("/admin/transcript/{transcript_id}")
async def delete_transcript(transcript_id: str, admin_key: str = Header(None)):
    # Verify admin key
    if admin_key != os.environ.get('ADMIN_KEY'):
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    try:
        # Find and delete the transcript
        result = await db.transcripts.delete_one({"id": transcript_id})
        
        if result.deleted_count == 0:
            # Try with _id as ObjectId if id didn't work
            raise HTTPException(status_code=404, detail=f"Transcript with ID {transcript_id} not found")
        
        # Return success response
        return {"status": "success", "message": f"Transcript {transcript_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting transcript: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
