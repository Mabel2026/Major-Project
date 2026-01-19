Upload.tsx

import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Upload.css";

type UploadType = "image" | "audio" | "video";

const Upload = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [uploadType, setUploadType] = useState<UploadType | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const openFilePicker = (type: UploadType) => {
    setUploadType(type);
    if (!fileInputRef.current) return;

    if (type === "image") fileInputRef.current.accept = "image/*";
    if (type === "audio") fileInputRef.current.accept = "audio/*";
    if (type === "video") fileInputRef.current.accept = "video/*";

    fileInputRef.current.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file || !uploadType) {
      alert("Please upload a file first.");
      return;
    }

    if (uploadType !== "audio") {
      alert("Image and Video analysis coming soon 🚧");
      return;
    }

    console.log("📁 Selected file:", file.name);

    // Clear old data
    localStorage.removeItem("audioAnalysis");

    const formData = new FormData();
    formData.append("file", file);

    setIsLoading(true);

    // Navigate to analyzing page FIRST
    navigate("/analyzing");

    try {
      console.log("📤 Sending request to backend...");
      
      const res = await fetch("http://127.0.0.1:8000/analyze/audio", {
        method: "POST",
        body: formData,
      });

      console.log("📥 Response status:", res.status);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      console.log("✅ Received data:", data);

      // Store in localStorage (Analyzing page will check this)
      localStorage.setItem("audioAnalysis", JSON.stringify(data));

      // The Analyzing page will automatically navigate to results
      // when it detects the data is ready

    } catch (err) {
      console.error("❌ Audio analysis failed:", err);
      
      // Use mock data for testing
      const mockData = {
        file_id: "mock_" + Date.now(),
        transcript: "This is a test transcript. The audio was successfully analyzed. It contains sensitive information like names and locations that should be redacted.",
        entities: [
          {text: "John Doe", type: "PERSON"},
          {text: "New York", type: "GPE"},
          {text: "123-456-7890", type: "PHONE"},
          {text: "john@email.com", type: "EMAIL"}
        ]
      };
      
      localStorage.setItem("audioAnalysis", JSON.stringify(mockData));
      
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="hero-wrapper">
      <div className="hero-card">
        {/* LEFT */}
        <div className="hero-left">
          <h1 className="brand">
            REDACT<span>LY</span>
          </h1>

          <h2>Your Media's Privacy Guardian</h2>

          <p>
            Detect and redact exposed faces, voices, phone numbers, and
            sensitive information before sharing your media.
          </p>

          <div className="upload-options">
            <button onClick={() => openFilePicker("image")}>
              Upload Image
            </button>

            <button onClick={() => openFilePicker("audio")}>
              Upload Audio
            </button>

            <button onClick={() => openFilePicker("video")}>
              Upload Video
            </button>
          </div>

          <button 
            className="primary-btn analyze-btn" 
            onClick={handleAnalyze}
            disabled={isLoading || !file}
          >
            {isLoading ? "Analyzing..." : "Analyze"}
          </button>

          {file && uploadType && (
            <div className="file-chip">
              Selected {uploadType}: {file.name}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            hidden
            onChange={handleFileChange}
          />
        </div>

        {/* RIGHT — ANIMATION PRESERVED */}
        <div className="hero-right">
          <div className="visual-card">
            <div className="scan-line"></div>
            <div className="node n1">VOICE</div>
            <div className="node n2">PII</div>
            <div className="node n3">LOCATION</div>
            <div className="shield-core">AI SCAN</div>
          </div>
          <div className="red-panel"></div>
        </div>
      </div>
    </section>
  );
};

export default Upload;