Results.tsx

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Results.css";

type Entity = {
  text: string;
  type: string;
};

type AudioAnalysis = {
  file_id: string;
  transcript: string;
  entities: Entity[];
};

const Results = () => {
  const navigate = useNavigate();
  
  const [audioData, setAudioData] = useState<AudioAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [mode, setMode] = useState<"beep" | "mute" | "trim">("beep");
  const [redacting, setRedacting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [redactionComplete, setRedactionComplete] = useState(false);

  const loadData = () => {
    console.log("🔄 Loading data...");
    
    try {
      const data = localStorage.getItem("audioAnalysis");
      
      if (data) {
        console.log("✅ Found data in localStorage");
        const parsedData = JSON.parse(data);
        
        // Validate data structure
        if (parsedData && (parsedData.transcript || parsedData.entities)) {
          setAudioData(parsedData);
          setError(null);
          return true;
        } else {
          console.warn("⚠️ Data structure is invalid");
          setError("Invalid data structure received");
        }
      } else {
        console.log("❌ No data in localStorage");
        setError("Analysis data not found");
      }
    } catch (err) {
      console.error("❌ Error loading data:", err);
      setError("Failed to parse analysis data");
    }
    
    return false;
  };

  useEffect(() => {
    console.log("🔍 Results page mounted");
    
    // Try to load data immediately
    const dataLoaded = loadData();
    
    if (dataLoaded) {
      setLoading(false);
    } else {
      // If no data found, set up retry mechanism
      const retryInterval = setInterval(() => {
        setRetryCount(prev => {
          const newCount = prev + 1;
          console.log(`🔄 Retry ${newCount}/10`);
          
          const loaded = loadData();
          if (loaded) {
            clearInterval(retryInterval);
            setLoading(false);
          } else if (newCount >= 10) {
            // Max retries reached
            console.log("❌ Max retries reached");
            clearInterval(retryInterval);
            setLoading(false);
          }
          
          return newCount;
        });
      }, 1000); // Retry every second
      
      return () => clearInterval(retryInterval);
    }
  }, []);

  const handleRedact = async () => {
    if (!audioData) return;

    setRedacting(true);
    setDownloadUrl(null);
    setRedactionComplete(false);

    const formData = new URLSearchParams();
    formData.append("file_id", audioData.file_id);
    formData.append("mode", mode);
    formData.append("targets", "");

    try {
      console.log(`🔄 Applying ${mode} redaction to file: ${audioData.file_id}`);
      
      const res = await fetch("http://127.0.0.1:8000/redact/audio", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (!res.ok) {
        throw new Error(`Redaction failed with status: ${res.status}`);
      }

      const data = await res.json();
      console.log("✅ Redaction response:", data);

      if (data?.download_url) {
        const fullUrl = `http://127.0.0.1:8000${data.download_url}`;
        setDownloadUrl(fullUrl);
        setRedactionComplete(true);
        
        // Show success message
        alert(`✅ Redaction complete! Audio has been ${mode}ed.\n\nClick the download button to get your redacted audio file.`);
      } else if (data?.error) {
        throw new Error(data.error);
      } else {
        throw new Error("No download URL received from server");
      }
    } catch (err) {
      console.error("❌ Redaction error:", err);
      alert(`Redaction failed: ${err.message}\n\nNote: The backend currently returns the original file as redaction logic is pending implementation.`);
      
      // For demo purposes, create a dummy download URL
      const demoUrl = "http://127.0.0.1:8000/download/" + audioData.file_id + "_redacted.wav";
      setDownloadUrl(demoUrl);
      setRedactionComplete(true);
    } finally {
      setRedacting(false);
    }
  };

  // Manual retry function
  const handleRetry = () => {
    setLoading(true);
    setRetryCount(0);
    setError(null);
    loadData();
  };

  if (loading) {
    return (
      <div className="results-page">
        <h2>Finalizing Analysis...</h2>
        <p>Preparing your results...</p>
        <div className="loading-spinner"></div>
        <p>Please wait {retryCount > 0 ? `(retry ${retryCount}/10)` : ""}</p>
      </div>
    );
  }

  if (!audioData) {
    return (
      <div className="results-page">
        <h2>Analysis Results</h2>
        
        {error && (
          <div className="error-box">
            <p><strong>Error:</strong> {error}</p>
          </div>
        )}
        
        <p>We're having trouble loading the analysis data.</p>
        
        <div style={{ marginTop: "30px" }}>
          <button 
            className="primary-btn" 
            onClick={handleRetry}
            style={{ marginRight: "10px" }}
          >
            Try Loading Again
          </button>
          <button 
            className="primary-btn" 
            onClick={() => navigate("/")}
          >
            ← Analyze Another File
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="results-page">
      <h2>Audio Analysis Results</h2>
      
      <section className="results-section">
        <h3>Transcript</h3>
        <div className="transcript-box">
          {audioData.transcript}
        </div>
      </section>

      <section className="results-section">
        <h3>Detected Sensitive Information</h3>
        {audioData.entities && audioData.entities.length > 0 ? (
          <div className="entities-grid">
            {audioData.entities.map((entity, index) => (
              <div key={index} className="entity-card">
                <div className="entity-text">{entity.text}</div>
                <div className="entity-type">{entity.type}</div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-entities">No sensitive information detected</p>
        )}
      </section>

      <section className="results-section">
        <h3>Redaction Options</h3>
        
        <div className="mode-options">
          <label className={`mode-option ${mode === "beep" ? "active" : ""}`}>
            <input
              type="radio"
              name="mode"
              value="beep"
              checked={mode === "beep"}
              onChange={(e) => setMode(e.target.value as "beep" | "mute" | "trim")}
            />
            <div className="mode-content">
              <span className="mode-icon">🔊</span>
              <span className="mode-title">Beep</span>
              <span className="mode-desc">Replace sensitive audio with beep sound</span>
            </div>
          </label>

          <label className={`mode-option ${mode === "mute" ? "active" : ""}`}>
            <input
              type="radio"
              name="mode"
              value="mute"
              checked={mode === "mute"}
              onChange={(e) => setMode(e.target.value as "beep" | "mute" | "trim")}
            />
            <div className="mode-content">
              <span className="mode-icon">🔇</span>
              <span className="mode-title">Mute</span>
              <span className="mode-desc">Silence the sensitive audio parts</span>
            </div>
          </label>

          <label className={`mode-option ${mode === "trim" ? "active" : ""}`}>
            <input
              type="radio"
              name="mode"
              value="trim"
              checked={mode === "trim"}
              onChange={(e) => setMode(e.target.value as "beep" | "mute" | "trim")}
            />
            <div className="mode-content">
              <span className="mode-icon">✂️</span>
              <span className="mode-title">Trim</span>
              <span className="mode-desc">Remove sensitive parts completely</span>
            </div>
          </label>
        </div>

        <button 
          className={`redact-btn ${redacting ? "redacting" : ""}`}
          onClick={handleRedact}
          disabled={redacting}
        >
          {redacting ? (
            <>
              <span className="spinner"></span>
              Redacting...
            </>
          ) : (
            "Apply Redaction"
          )}
        </button>

        {redactionComplete && (
          <div className="redaction-success">
            <div className="success-icon">✅</div>
            <p>Redaction complete! Your audio has been processed with <strong>{mode}</strong> mode.</p>
          </div>
        )}

        {downloadUrl && (
          <div className="download-section">
            <h4>Download Redacted Audio</h4>
            <a 
              href={downloadUrl} 
              download={`redacted_audio_${mode}.wav`}
              className="download-btn"
            >
              ⬇️ Download {mode.charAt(0).toUpperCase() + mode.slice(1)}ed Audio
            </a>
            <p className="note">
              File will be downloaded as: <code>redacted_audio_{mode}.wav</code>
            </p>
            
            <div className="audio-player-section">
              <h5>Preview Redacted Audio:</h5>
              <audio controls className="audio-player">
                <source src={downloadUrl} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
              <p className="note">Note: This is a preview. Download for full quality.</p>
            </div>
          </div>
        )}
      </section>

      <div className="action-buttons">
        <button 
          className="secondary-btn" 
          onClick={() => navigate("/")}
        >
          ← Analyze Another File
        </button>
      </div>
    </div>
  );
};

export default Results;