import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoCard = ({ video, onClick }) => {
  const defaultThumbnail = "https://via.placeholder.com/320x180?text=No+Thumbnail";
  
  return (
    <div 
      className="bg-white rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300 cursor-pointer"
      onClick={() => onClick(video)}
    >
      <div className="relative pb-[56.25%]">
        <img 
          src={video.thumbnail_url || defaultThumbnail} 
          alt={video.title || "Video thumbnail"} 
          className="absolute h-full w-full object-cover"
          onError={(e) => { e.target.src = defaultThumbnail }}
        />
      </div>
      <div className="p-3">
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

const Home = () => {
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

  return (
    <div className="max-w-5xl mx-auto p-4 bg-gray-50 min-h-screen">
      <header className="text-center mb-8 pt-8">
        <h1 className="text-3xl font-bold text-indigo-700">🎬 YouTube Video Summarizer</h1>
        <p className="text-gray-600 mt-2">✨ Get a concise summary from any YouTube video transcript</p>
      </header>

      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <form onSubmit={handleSummarize} className="mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="🔗 Paste YouTube URL here (e.g. https://www.youtube.com/watch?v=...)"
              className="flex-grow p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            />
            <button
              type="submit"
              disabled={isLoading}
              className={`px-6 py-3 rounded-md text-white font-medium ${
                isLoading 
                  ? "bg-gray-400 cursor-not-allowed" 
                  : "bg-indigo-600 hover:bg-indigo-700"
              }`}
            >
              {isLoading ? "⏳ Processing..." : "✨ Summarize"}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
            ⚠️ {error}
          </div>
        )}

        <div className="flex justify-end mb-4">
          <button 
            onClick={() => setShowHistory(!showHistory)}
            className="text-sm text-indigo-600 hover:text-indigo-800 underline"
          >
            {showHistory ? "📁 Hide History" : "📋 Show History"}
          </button>
        </div>

        {showHistory && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-3">📚 Previously Summarized Videos</h2>
            {history.length === 0 ? (
              <p className="text-gray-500">No history available</p>
            ) : (
              <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-md divide-y">
                {history.map((item) => (
                  <div 
                    key={item.id} 
                    className="p-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => loadFromHistory(item)}
                  >
                    <div className="flex items-start">
                      {item.thumbnail_url && (
                        <img 
                          src={item.thumbnail_url} 
                          alt={item.title || "Video thumbnail"} 
                          className="w-16 h-9 object-cover rounded mr-2 flex-shrink-0"
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
          <div className="mt-6">
            {currentVideo && currentVideo.title && (
              <div className="flex items-start mb-4 bg-gray-50 p-3 rounded-md">
                {currentVideo.thumbnail_url && (
                  <img 
                    src={currentVideo.thumbnail_url} 
                    alt={currentVideo.title} 
                    className="w-24 h-14 object-cover rounded mr-3 flex-shrink-0"
                    onError={(e) => {e.target.src = "https://via.placeholder.com/240x140"}}
                  />
                )}
                <div>
                  <h2 className="font-medium text-gray-900">{currentVideo.title}</h2>
                  {currentVideo.channel && (
                    <p className="text-sm text-gray-600">{currentVideo.channel}</p>
                  )}
                  {isCached && (
                    <span className="inline-block mt-1 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      ⚡ Showing cached results
                    </span>
                  )}
                </div>
              </div>
            )}
            
            <div className="flex border-b border-gray-200 mb-4">
              <button
                onClick={() => setActiveSection("summary")}
                className={`py-2 px-4 font-medium ${
                  activeSection === "summary"
                    ? "text-indigo-600 border-b-2 border-indigo-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                📝 Summary
              </button>
              <button
                onClick={() => setActiveSection("transcript")}
                className={`py-2 px-4 font-medium ${
                  activeSection === "transcript"
                    ? "text-indigo-600 border-b-2 border-indigo-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                📃 Transcript
              </button>
            </div>

            {activeSection === "summary" && (
              <div className="bg-gray-50 p-4 rounded-md whitespace-pre-line">
                <h2 className="text-xl font-semibold mb-3">📝 Summary</h2>
                <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: summary.replace(/\n/g, '<br>') }}></div>
              </div>
            )}

            {activeSection === "transcript" && (
              <div className="bg-gray-50 p-4 rounded-md">
                <h2 className="text-xl font-semibold mb-3">📃 Transcript</h2>
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
        <div className="mb-10">
          <h2 className="text-xl font-semibold mb-4">🎞️ Recently Summarized Videos</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-4">
            {recentVideos.map((video) => (
              <VideoCard 
                key={video.id} 
                video={video} 
                onClick={loadFromHistory} 
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
