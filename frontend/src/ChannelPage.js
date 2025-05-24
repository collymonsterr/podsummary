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
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex justify-center items-center">
        <div className="text-center p-8 bg-white rounded-xl shadow-md">
          <div className="inline-block animate-spin mb-4">
            <svg className="w-10 h-10 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p className="text-gray-700 font-medium">Loading channel videos...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-5xl mx-auto p-6">
          <div className="mb-6 pt-4">
            <Link to="/" className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Back to Home
            </Link>
          </div>
          <div className="bg-red-50 text-red-700 p-6 rounded-xl border border-red-100 shadow-md">
            <h2 className="text-xl font-bold mb-2">Error</h2>
            <p>{error}</p>
          </div>
        </div>
      </div>
    );
  }
  
  if (videos.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-5xl mx-auto p-6">
          <div className="mb-6 pt-4">
            <Link to="/" className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Back to Home
            </Link>
          </div>
          <div className="text-center p-10 bg-white rounded-xl shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
            <h2 className="text-xl font-bold mb-4 text-gray-800">No videos found</h2>
            <p className="text-gray-600">We couldn't find any videos for this channel. Please check the URL and try again.</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="hero-gradient text-white py-10 px-4 shadow-md">
        <div className="max-w-5xl mx-auto">
          <div className="mb-4">
            <Link to="/" className="text-white hover:text-gray-200 font-medium flex items-center gap-1 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Back to Home
            </Link>
          </div>
          
          <h1 className="text-3xl font-bold">🎧 Latest Podcasts from {channel}</h1>
        </div>
      </div>
      
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in">
          {videos.map((video) => (
            <div key={video.id || video.position} className="bg-white rounded-xl shadow-md overflow-hidden card-hover">
              <div className="relative">
                <img 
                  src={video.thumbnail?.static || video.thumbnail || `https://img.youtube.com/vi/${video.id}/maxresdefault.jpg`} 
                  alt={video.title} 
                  className="w-full h-48 object-cover"
                  onError={(e) => {e.target.src = "https://via.placeholder.com/480x270?text=No+Thumbnail"}}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
              </div>
              
              <div className="p-5">
                <h2 className="text-lg font-semibold mb-2 line-clamp-2 text-gray-800">{video.title}</h2>
                
                <div className="text-sm text-gray-500 mb-4">
                  {video.channel?.name || channel}
                </div>
                
                <div className="flex justify-between items-center gap-4">
                  <button
                    onClick={() => summarizeVideo(video.link)}
                    className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium text-center"
                  >
                    Get Summary
                  </button>
                  
                  <a 
                    href={video.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 border border-red-500 text-red-600 px-4 py-2 rounded-lg hover:bg-red-50 transition-colors font-medium text-center"
                  >
                    Watch on YouTube
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Footer */}
        <footer className="text-center py-8 text-gray-500 text-sm animate-fade-in">
          <p>© {new Date().getFullYear()} Podbrief - Get concise summaries of your favorite podcasts</p>
        </footer>
      </div>
    </div>
  );
};

export default ChannelPage;
