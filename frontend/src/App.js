import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from "react-router-dom";
import axios from "axios";
import ChannelPage from "./ChannelPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoCard = ({ video, onClick, onDelete, isAdmin }) => {
  const defaultThumbnail = "https://via.placeholder.com/320x180?text=No+Thumbnail";
  
  const handleDelete = (e) => {
    e.stopPropagation();
    onDelete(video.id);
  };
  
  return (
    <div 
      className="bg-white rounded-xl overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer relative card-hover"
      onClick={() => onClick(video)}
    >
      {isAdmin && (
        <button 
          className="absolute top-2 right-2 bg-red-500 text-white p-1 rounded-full w-6 h-6 flex items-center justify-center z-10 hover:bg-red-600"
          onClick={handleDelete}
          title="Delete video"
        >
          ×
        </button>
      )}
      <div className="relative pb-[56.25%]">
        <img 
          src={video.thumbnail_url || defaultThumbnail} 
          alt={video.title || "Video thumbnail"} 
          className="absolute h-full w-full object-cover"
          onError={(e) => { e.target.src = defaultThumbnail }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
      </div>
      <div className="p-4">
        <h3 className="font-medium text-gray-900 line-clamp-2 text-sm">
          {video.title || "Unknown Title"}
        </h3>
        <p className="text-gray-600 text-xs mt-1">
          {video.channel || "Unknown Channel"}
        </p>
      </div>
    </div>
  );
};

// Wrapper component that has access to useNavigate
const HomeWithNavigation = () => {
  const navigate = useNavigate();
  return <Home navigate={navigate} />;
};

const Home = ({ navigate }) => {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [recentVideos, setRecentVideos] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeSection, setActiveSection] = useState("summary");
  const [isCached, setIsCached] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminKey, setAdminKey] = useState("");
  const [channelUrl, setChannelUrl] = useState("");
  
  // Set document title on load
  useEffect(() => {
    document.title = "Podbrief - Podcast Summaries";
  }, []);

  // Check for video param in URL 
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const videoParam = params.get("video");
    
    if (videoParam) {
      setYoutubeUrl(videoParam);
      // Automatically trigger summarization for the video in URL
      handleSummarizeFromURL(videoParam);
    }
  }, []);
  
  // Function to handle summarization from URL parameter
  const handleSummarizeFromURL = async (url) => {
    setIsLoading(true);
    setError("");
    setTranscript("");
    setSummary("");
    setIsCached(false);
    setCurrentVideo(null);
    
    try {
      const response = await axios.post(`${API}/summarize`, {
        youtube_url: url
      });
      
      setTranscript(response.data.transcript);
      setSummary(response.data.summary);
      setIsCached(response.data.is_cached);
      
      // Set current video data
      setCurrentVideo({
        title: response.data.title,
        channel: response.data.channel,
        thumbnail_url: response.data.thumbnail_url,
        video_id: response.data.video_id,
        url: response.data.url
      });
      
      // Refresh history after new summary
      const historyResponse = await axios.get(`${API}/history`);
      const historyData = historyResponse.data;
      setHistory(historyData);
      setRecentVideos(historyData.slice(0, 6));
      
    } catch (e) {
      console.error("Summarization error:", e);
      setError(e.response?.data?.detail || "Failed to get summary. Please check the URL and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Check if admin key is in localStorage on load
  useEffect(() => {
    const storedAdminKey = localStorage.getItem("adminKey");
    if (storedAdminKey) {
      setAdminKey(storedAdminKey);
      setIsAdmin(true);
    }
  }, []);

  // Check API status on load and load history
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await axios.get(`${API}/`);
        console.log("API Status:", response.data.message);
      } catch (e) {
        console.error("API Error:", e);
        setError("Could not connect to API service. Please try again later.");
      }
    };

    const loadHistory = async () => {
      try {
        const response = await axios.get(`${API}/history`);
        const historyData = response.data;
        
        // Set both full history and recent videos
        setHistory(historyData);
        setRecentVideos(historyData.slice(0, 6));
      } catch (e) {
        console.error("Error loading history:", e);
      }
    };

    checkApiStatus();
    loadHistory();
  }, []);

  const handleSummarize = async (e) => {
    e.preventDefault();
    
    if (!youtubeUrl || !youtubeUrl.includes("youtube.com") && !youtubeUrl.includes("youtu.be")) {
      setError("Please enter a valid YouTube URL");
      return;
    }
    
    setIsLoading(true);
    setError("");
    setTranscript("");
    setSummary("");
    setIsCached(false);
    setCurrentVideo(null);
    
    try {
      const response = await axios.post(`${API}/summarize`, {
        youtube_url: youtubeUrl
      });
      
      setTranscript(response.data.transcript);
      setSummary(response.data.summary);
      setIsCached(response.data.is_cached);
      
      // Set current video data
      setCurrentVideo({
        title: response.data.title,
        channel: response.data.channel,
        thumbnail_url: response.data.thumbnail_url,
        video_id: response.data.video_id,
        url: response.data.url
      });
      
      // Refresh history after new summary
      const historyResponse = await axios.get(`${API}/history`);
      const historyData = historyResponse.data;
      setHistory(historyData);
      setRecentVideos(historyData.slice(0, 6));
      
    } catch (e) {
      console.error("Summarization error:", e);
      setError(e.response?.data?.detail || "Failed to get summary. Please check the URL and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadFromHistory = (item) => {
    setYoutubeUrl(item.url);
    setTranscript(item.transcript);
    setSummary(item.summary);
    setShowHistory(false);
    setIsCached(true);
    setCurrentVideo({
      title: item.title,
      channel: item.channel,
      thumbnail_url: item.thumbnail_url,
      video_id: item.video_id,
      url: item.url
    });
  };
  
  const toggleAdminMode = () => {
    if (isAdmin) {
      // Log out of admin mode
      setIsAdmin(false);
      setAdminKey("");
      localStorage.removeItem("adminKey");
    } else {
      // Prompt for admin key
      const key = prompt("Enter admin key:");
      if (key) {
        setAdminKey(key);
        setIsAdmin(true);
        localStorage.setItem("adminKey", key);
      }
    }
  };
  
  const handleDeleteVideo = async (videoId) => {
    if (!isAdmin || !adminKey) {
      alert("Admin privileges required to delete videos");
      return;
    }
    
    try {
      const confirmed = window.confirm("Are you sure you want to delete this video?");
      if (!confirmed) return;
      
      // Make API call to delete the video
      await axios.delete(`${API}/admin/transcript/${videoId}`, {
        headers: {
          "admin-key": adminKey
        }
      });
      
      // Update both history lists after deletion
      const historyResponse = await axios.get(`${API}/history`);
      const historyData = historyResponse.data;
      setHistory(historyData);
      setRecentVideos(historyData.slice(0, 6));
      
      // Show success message
      alert("Video deleted successfully");
      
      // If the deleted video is the current one, clear it
      if (currentVideo && videoId === currentVideo.id) {
        setTranscript("");
        setSummary("");
        setCurrentVideo(null);
      }
    } catch (error) {
      console.error("Error deleting video:", error);
      alert(`Failed to delete video: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Admin button */}
      <button 
        onClick={toggleAdminMode}
        className={`fixed top-4 right-4 z-50 text-sm px-3 py-1.5 rounded-md transition-colors shadow-sm ${
          isAdmin 
            ? "bg-red-500 text-white hover:bg-red-600" 
            : "bg-white text-gray-700 hover:bg-gray-100"
        }`}
        title={isAdmin ? "Exit admin mode" : "Enter admin mode"}
      >
        {isAdmin ? "👑 Admin Mode" : "👤 Admin"}
      </button>
      
      {/* Hero Section */}
      <div className="hero-gradient text-white py-16 px-4 shadow-md animate-fade-in">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">🎧 Podbrief</h1>
          <p className="text-xl md:text-2xl max-w-2xl mx-auto opacity-90">
            Concise summaries of your favourite podcasts—so you only spend time on the episodes that matter.
          </p>
        </div>
      </div>
      
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Main input form */}
        <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8 -mt-10 mb-10 glass-card animate-fade-in">
          <form onSubmit={handleSummarize} className="mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="🔗 Paste YouTube URL with podcast (e.g. https://www.youtube.com/watch?v=...)"
                className="flex-grow p-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 input-shadow text-gray-700 shadow-sm"
                required
              />
              <button
                type="submit"
                disabled={isLoading}
                className={`px-8 py-4 rounded-xl text-white font-medium transition-all shadow-md ${
                  isLoading 
                    ? "bg-gray-400 cursor-not-allowed" 
                    : "bg-indigo-600 hover:bg-indigo-700 hover:shadow-lg"
                }`}
              >
                {isLoading ? 
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </span> : 
                  "✨ Get Summary"
                }
              </button>
            </div>
          </form>

          {error && (
            <div className="bg-red-50 text-red-700 p-5 rounded-xl mb-6 border border-red-100 animate-fade-in">
              ⚠️ {error}
            </div>
          )}

          <div className="flex justify-end mb-4">
            <button 
              onClick={() => setShowHistory(!showHistory)}
              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
            >
              {showHistory ? 
                <><span>📁</span> Hide History</> : 
                <><span>📋</span> Show History</>
              }
            </button>
          </div>

          {showHistory && (
            <div className="mb-6 animate-fade-in">
              <h2 className="text-xl font-semibold mb-4">📚 Previously Summarized Podcasts</h2>
              {history.length === 0 ? (
                <p className="text-gray-500 p-4 bg-gray-50 rounded-xl">No history available</p>
              ) : (
                <div className="max-h-72 overflow-y-auto border border-gray-100 rounded-xl divide-y shadow-sm">
                  {history.map((item) => (
                    <div 
                      key={item.id} 
                      className="p-4 hover:bg-gray-50 cursor-pointer relative transition-colors"
                      onClick={() => loadFromHistory(item)}
                    >
                      {isAdmin && (
                        <button 
                          className="absolute top-3 right-3 bg-red-500 text-white p-1 rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 z-10 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteVideo(item.id);
                          }}
                          title="Delete video"
                        >
                          ×
                        </button>
                      )}
                      <div className="flex items-start">
                        {item.thumbnail_url && (
                          <img 
                            src={item.thumbnail_url} 
                            alt={item.title || "Video thumbnail"} 
                            className="w-20 h-12 object-cover rounded-lg mr-3 flex-shrink-0 shadow-sm"
                            onError={(e) => {e.target.src = "https://via.placeholder.com/160x90"}}
                          />
                        )}
                        <div className="flex-grow">
                          <div className="line-clamp-1 text-gray-900 font-medium">
                            {item.title || item.url}
                          </div>
                          {item.channel && (
                            <div className="line-clamp-1 text-xs text-gray-600 mt-1">
                              {item.channel}
                            </div>
                          )}
                          <div className="text-xs text-gray-500 mt-1">
                            🕒 {new Date(item.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {(summary || transcript) && (
            <div className="mt-8 animate-fade-in">
              {currentVideo && currentVideo.title && (
                <div className="flex items-start mb-6 bg-gray-50 p-5 rounded-xl">
                  {currentVideo.thumbnail_url && (
                    <img 
                      src={currentVideo.thumbnail_url} 
                      alt={currentVideo.title} 
                      className="w-32 h-18 object-cover rounded-lg mr-4 flex-shrink-0 shadow-sm"
                      onError={(e) => {e.target.src = "https://via.placeholder.com/240x140"}}
                    />
                  )}
                  <div>
                    <h2 className="font-semibold text-gray-900 text-lg">{currentVideo.title}</h2>
                    {currentVideo.channel && (
                      <p className="text-sm text-gray-600 mt-1">{currentVideo.channel}</p>
                    )}
                    {isCached && (
                      <span className="inline-block mt-2 bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full">
                        ⚡ Showing cached results
                      </span>
                    )}
                  </div>
                </div>
              )}
              
              <div className="flex border-b border-gray-200 mb-6">
                <button
                  onClick={() => setActiveSection("summary")}
                  className={`py-3 px-5 font-medium transition-colors ${
                    activeSection === "summary"
                      ? "text-indigo-600 border-b-2 border-indigo-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  📝 Summary
                </button>
                <button
                  onClick={() => setActiveSection("transcript")}
                  className={`py-3 px-5 font-medium transition-colors ${
                    activeSection === "transcript"
                      ? "text-indigo-600 border-b-2 border-indigo-600"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  📃 Transcript
                </button>
              </div>

              {activeSection === "summary" && (
                <div className="bg-gray-50 p-6 rounded-xl whitespace-pre-line border border-gray-100 shadow-sm">
                  <h2 className="text-xl font-semibold mb-4">📝 Summary</h2>
                  <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: summary.replace(/\n/g, '<br>') }}></div>
                </div>
              )}

              {activeSection === "transcript" && (
                <div className="bg-gray-50 p-6 rounded-xl border border-gray-100 shadow-sm">
                  <h2 className="text-xl font-semibold mb-4">📃 Transcript</h2>
                  <div className="max-h-96 overflow-y-auto whitespace-pre-line">
                    {transcript}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Recent Videos Section */}
        {recentVideos.length > 0 && (
          <div className="mb-12 animate-fade-in">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">🎧 Recently Summarized Podcasts</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {recentVideos.map((video) => (
                <VideoCard 
                  key={video.id} 
                  video={video} 
                  onClick={loadFromHistory}
                  onDelete={handleDeleteVideo}
                  isAdmin={isAdmin}
                />
              ))}
            </div>
          </div>
        )}

        {/* Channel Search Section */}
        <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-12 glass-card animate-fade-in">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">🎧 Summarize an Entire Channel</h2>
          <p className="text-gray-600 mb-6">Enter any YouTube channel URL to see the latest videos and get summaries.</p>
          
          <form onSubmit={(e) => {
            e.preventDefault();
            if (channelUrl) {
              navigate(`/channel?url=${encodeURIComponent(channelUrl)}`);
            }
          }} className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              value={channelUrl}
              onChange={(e) => setChannelUrl(e.target.value)}
              placeholder="Paste YouTube channel URL (e.g., https://www.youtube.com/@channelname)"
              className="flex-grow p-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 input-shadow text-gray-700 shadow-sm"
              required
            />
            <button
              type="submit"
              className="px-8 py-4 rounded-xl text-white font-medium bg-indigo-600 hover:bg-indigo-700 transition-all shadow-md hover:shadow-lg"
            >
              📺 Get Channel Summaries
            </button>
          </form>
        </div>
        
        {/* Footer */}
        <footer className="text-center py-6 text-gray-500 text-sm animate-fade-in">
          <p>© {new Date().getFullYear()} Podbrief - Get concise summaries of your favorite podcasts</p>
        </footer>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomeWithNavigation />} />
          <Route path="/channel" element={<ChannelPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
