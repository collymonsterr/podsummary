import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeSection, setActiveSection] = useState("summary");

  // Check API status on load
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
        setHistory(response.data);
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
    
    try {
      const response = await axios.post(`${API}/summarize`, {
        youtube_url: youtubeUrl
      });
      
      setTranscript(response.data.transcript);
      setSummary(response.data.summary);
      
      // Refresh history after new summary
      const historyResponse = await axios.get(`${API}/history`);
      setHistory(historyResponse.data);
      
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
  };

  return (
    <div className="max-w-4xl mx-auto p-4 bg-gray-50 min-h-screen">
      <header className="text-center mb-8 pt-8">
        <h1 className="text-3xl font-bold text-indigo-700">YouTube Video Summarizer</h1>
        <p className="text-gray-600 mt-2">Get a concise summary from any YouTube video transcript</p>
      </header>

      <div className="bg-white shadow-md rounded-lg p-6 mb-8">
        <form onSubmit={handleSummarize} className="mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="Paste YouTube URL here (e.g. https://www.youtube.com/watch?v=...)"
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
              {isLoading ? "Processing..." : "Summarize"}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-md mb-6">
            {error}
          </div>
        )}

        <div className="flex justify-end mb-4">
          <button 
            onClick={() => setShowHistory(!showHistory)}
            className="text-sm text-indigo-600 hover:text-indigo-800 underline"
          >
            {showHistory ? "Hide History" : "Show History"}
          </button>
        </div>

        {showHistory && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-3">Previously Summarized Videos</h2>
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
                    <div className="line-clamp-1 text-indigo-600">{item.url}</div>
                    <div className="line-clamp-1 text-sm text-gray-500">
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {(summary || transcript) && (
          <div className="mt-6">
            <div className="flex border-b border-gray-200 mb-4">
              <button
                onClick={() => setActiveSection("summary")}
                className={`py-2 px-4 font-medium ${
                  activeSection === "summary"
                    ? "text-indigo-600 border-b-2 border-indigo-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Summary
              </button>
              <button
                onClick={() => setActiveSection("transcript")}
                className={`py-2 px-4 font-medium ${
                  activeSection === "transcript"
                    ? "text-indigo-600 border-b-2 border-indigo-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Transcript
              </button>
            </div>

            {activeSection === "summary" && (
              <div className="bg-gray-50 p-4 rounded-md whitespace-pre-line">
                <h2 className="text-xl font-semibold mb-3">Summary</h2>
                {summary}
              </div>
            )}

            {activeSection === "transcript" && (
              <div className="bg-gray-50 p-4 rounded-md">
                <h2 className="text-xl font-semibold mb-3">Transcript</h2>
                <div className="max-h-96 overflow-y-auto whitespace-pre-line">
                  {transcript}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
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
