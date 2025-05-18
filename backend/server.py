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
        # If transcript is very long, truncate it to avoid token limits
        max_tokens = 16000  # Maximum context for newer models
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
    except Exception as e:
        logging.error(f"Error in summarizing text: {str(e)}")
        
        # Fallback to extractive summarization
        try:
            # Simple extractive summarization as fallback
            sentences = text.split('. ')
            
            # If very short transcript, return as is
            if len(sentences) <= 5:
                return "Transcript is too short to summarize effectively. Here it is in full: " + text
            
            # Take first sentence (usually introduction)
            summary = [sentences[0]]
            
            # Take a sentence from every ~10% of the transcript
            if len(sentences) > 10:
                segment_size = len(sentences) // 10
                for i in range(1, 10):
                    idx = min(i * segment_size, len(sentences) - 1)
                    summary.append(sentences[idx])
            else:
                # For shorter transcripts, take every other sentence
                summary.extend([s for i, s in enumerate(sentences[1:]) if i % 2 == 0])
            
            # Add the last sentence (usually a conclusion)
            if sentences[-1] not in summary:
                summary.append(sentences[-1])
            
            return "Note: This is an extractive summary created due to API limits.\n\n" + ". ".join(summary) + "."
        except Exception as summarization_error:
            logging.error(f"Fallback summarization error: {str(summarization_error)}")
            return "Error generating summary. The transcript was processed but could not be summarized. You can view the full transcript in the Transcript tab."

# Route to get transcript and summary from YouTube URL
@api_router.post("/summarize", response_model=TranscriptResponse)
async def summarize_youtube_video(request: VideoRequest):
    try:
        # Extract YouTube video ID from URL
        try:
            video_id = extract_video_id(request.youtube_url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Check if we already have this video in our database
        existing = await db.transcripts.find_one({"video_id": video_id})
        if existing:
            return TranscriptResponse(
                transcript=existing["transcript"],
                summary=existing["summary"],
                video_id=existing["video_id"],
                url=existing["url"]
            )
        
        try:
            # Get transcript from YouTube
            transcript = await get_transcript(video_id)
            
            # Generate summary using OpenAI
            summary = await summarize_text(transcript)
            
            # Store in database
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
        except HTTPException as e:
            # Re-raise HTTP exceptions with their status codes
            raise e
        except Exception as e:
            # Log the error and return a 500 status
            logging.error(f"Error processing valid YouTube URL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
            
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
