from fastapi import FastAPI, APIRouter, HTTPException
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

class StoredTranscript(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    url: str
    transcript: str
    summary: str
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

# Get transcript using SearchAPI.io
async def get_transcript(video_id):
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "youtube_transcripts",
        "api_key": searchapi_key,
        "video_id": video_id,
        "lang": "en"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to get transcript: {response.text}"
        )
        
    data = response.json()
    
    if 'transcripts' not in data or not data['transcripts']:
        raise HTTPException(
            status_code=400,
            detail="No transcript found for this video"
        )
    
    # Extract text from transcript segments and join with spaces
    # Process segments in order of start time to ensure proper sequence
    segments = sorted(data['transcripts'], key=lambda x: x.get('start', 0))
    full_transcript = " ".join([segment.get('text', '') for segment in segments])
    return full_transcript

# Summarize text using OpenAI's API or a fallback method
async def summarize_text(text):
    try:
        # First try OpenAI API
        max_tokens = 8000  # Reduced context size for gpt-3.5-turbo
        if len(text) > max_tokens * 4:  # Approximate character count
            text = text[:max_tokens * 4]  # Truncate to fit within context window
            
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes YouTube video transcripts. Create a concise but comprehensive summary that captures the key points, main arguments, and important details from the transcript."},
                {"role": "user", "content": f"Please summarize this transcript: {text}"}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as openai_error:
        logging.error(f"OpenAI API error: {str(openai_error)}")
        
        # Special handling for song lyrics
        if "♪" in text:
            return "This appears to be a song with lyrics. Here's a summary of the key lyrics:\n\n" + summarize_song_lyrics(text)
        
        # Simple extractive summarization fallback that will always work
        logging.info("Using basic fallback summarization method")
        try:
            # Split text into chunks - use a simple period split if it's a song lyrics or similar
            chunks = text.split('. ')
            
            # For very short text, just return it
            if len(text) < 500 or len(chunks) < 5:
                return "The transcript is too short to summarize effectively. Here it is in full:\n\n" + text
                
            # Create a simple extractive summary
            summary_chunks = []
            
            # Always take the first chunk (often contains title or intro)
            if chunks[0]:
                summary_chunks.append(chunks[0])
                
            # Take samples throughout the text
            if len(chunks) > 10:
                # For longer texts, take samples at regular intervals
                sample_interval = max(1, len(chunks) // 5)
                for i in range(sample_interval, len(chunks), sample_interval):
                    if chunks[i].strip():
                        summary_chunks.append(chunks[i].strip())
            else:
                # For shorter texts, take every other chunk
                for i in range(1, len(chunks), 2):
                    if chunks[i].strip():
                        summary_chunks.append(chunks[i].strip())
            
            # Always include the last chunk if not already included (often contains conclusion)
            if chunks[-1] and chunks[-1] not in summary_chunks:
                summary_chunks.append(chunks[-1])
                
            # Join the summary chunks with periods where needed
            processed_chunks = []
            for chunk in summary_chunks:
                chunk = chunk.strip()
                if chunk and not chunk.endswith(('.', '!', '?', '"', '♪')):
                    chunk += '.'
                if chunk:
                    processed_chunks.append(chunk)
            
            # Join all chunks with spaces
            final_summary = " ".join(processed_chunks)
            
            # Add a note about the fallback method
            return "Note: This is an automatic extraction of key points from the transcript (OpenAI summarization unavailable).\n\n" + final_summary
            
        except Exception as fallback_error:
            logging.error(f"Error in fallback summarization: {str(fallback_error)}")
            # Ultimate fallback - return a message that still allows the user to see the transcript
            return "Sorry, we couldn't generate a summary for this video. Please check the transcript tab to see the full text."

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
        return "\n".join(unique_lyrics)
    
    # Otherwise, take representative samples
    summary = []
    
    # Always include first line if available
    if unique_lyrics and len(unique_lyrics) > 0:
        summary.append(unique_lyrics[0])
    
    # Take samples at regular intervals
    if len(unique_lyrics) > 5:
        interval = max(1, len(unique_lyrics) // 5)
        for i in range(interval, len(unique_lyrics), interval):
            summary.append(unique_lyrics[i])
    
    # Always include last line if not already included
    if unique_lyrics and unique_lyrics[-1] not in summary:
        summary.append(unique_lyrics[-1])
    
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
        
        # Check if we already have this video's transcript in our database
        existing = await db.transcripts.find_one({"video_id": video_id})
        transcript = ""
        
        if existing and "transcript" in existing and existing["transcript"]:
            # Use the cached transcript
            transcript = existing["transcript"]
        else:
            # Get transcript from YouTube
            try:
                transcript = await get_transcript(video_id)
            except Exception as e:
                logging.error(f"Error getting transcript: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Always generate a new summary (not using cached summary)
        summary = await summarize_text(transcript)
        
        # Store or update in database
        if existing:
            # Update the existing record with the new summary
            await db.transcripts.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "summary": summary,
                    "timestamp": datetime.utcnow()
                }}
            )
        else:
            # Create a new record
            transcript_obj = StoredTranscript(
                video_id=video_id,
                url=request.youtube_url,
                transcript=transcript,
                summary=summary
            )
            await db.transcripts.insert_one(transcript_obj.dict())
        
        return TranscriptResponse(
            transcript=transcript,
            summary=summary,
            video_id=video_id,
            url=request.youtube_url
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
    return [StoredTranscript(**item) for item in history]

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "YouTube Summarizer API is running"}

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
