import { useState, useEffect } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ChannelPage = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [channel, setChannel] = useState("");
  const [error, setError] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchChannelVideos = async () => {
      try {
        const params = new URLSearchParams(location.search);
        const url = params.get("url");
        
        if (!url) {
          setError("No channel URL provided");
          setLoading(false);
          return;
        }
        
        // Fetch channel videos
        const response = await axios.post(`${API}/channel-videos`, {
          channel_url: url
        });
        
        setChannel(response.data.channel_name);
        setVideos(response.data.videos);
      } catch (e) {
        console.error("Error fetching channel videos:", e);
        setError(e.response?.data?.detail || "Failed to fetch channel videos");
      } finally {
        setLoading(false);
      }
    };
    
    fetchChannelVideos();
  }, [location.search]);
  
  // Function to summarize a single video
  const summarizeVideo = (videoUrl) => {
    navigate(`/?video=${encodeURIComponent(videoUrl)}`);
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="text-3xl animate-pulse mb-4">⏳</div>
          <p>Loading channel videos...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="max-w-5xl mx-auto p-4">
        <div className="mb-6">
          <Link to="/" className="text-indigo-600 hover:underline">← Back to Home</Link>
        </div>
        <div className="bg-red-50 text-red-700 p-6 rounded-md">
          <h2 className="text-xl font-semibold mb-2">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }
  
  if (videos.length === 0) {
    return (
      <div className="max-w-5xl mx-auto p-4">
        <div className="mb-6">
          <Link to="/" className="text-indigo-600 hover:underline">← Back to Home</Link>
        </div>
        <div className="text-center p-8">
          <h2 className="text-xl font-semibold mb-4">No videos found</h2>
          <p>We couldn't find any videos for this channel. Please check the URL and try again.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-5xl mx-auto p-4">
      <div className="mb-6">
        <Link to="/" className="text-indigo-600 hover:underline">← Back to Home</Link>
      </div>
      
      <h1 className="text-2xl font-bold mb-6">🎧 Latest Podcasts from {channel}</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {videos.map((video) => (
          <div key={video.id || video.position} className="bg-white rounded-lg shadow-md overflow-hidden">
            <img 
              src={video.thumbnail?.static || video.thumbnail || `https://img.youtube.com/vi/${video.id}/maxresdefault.jpg`} 
              alt={video.title} 
              className="w-full h-48 object-cover"
              onError={(e) => {e.target.src = "https://via.placeholder.com/480x270?text=No+Thumbnail"}}
            />
            
            <div className="p-4">
              <h2 className="text-lg font-semibold mb-2 line-clamp-2">{video.title}</h2>
              
              <div className="text-sm text-gray-500 mb-2">
                {video.channel?.name || channel}
              </div>
              
              <div className="flex justify-between items-center mt-4">
                <button
                  onClick={() => summarizeVideo(video.link)}
                  className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
                >
                  Get Summary
                </button>
                
                <a 
                  href={video.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-red-600 hover:underline"
                >
                  Watch on YouTube
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChannelPage;