import React, { useState } from "react";
import axios from "axios";

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResponse(null);

    try {
      const res = await axios.post("http://127.0.0.1:5000/add_video", {
        youtube_url: youtubeUrl,
      });
      setResponse(res.data);
    } catch (err) {
      setError("Bir hata oluştu: " + (err.response?.data.error || err.message));
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center">
      <div className="bg-white shadow-lg rounded-lg p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4 text-center text-blue-600">
          YouTube Video Özetleme
        </h1>
        <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
          <label className="text-gray-700">
            YouTube URL:
            <input
              type="text"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              required
              className="mt-2 px-3 py-2 border rounded-md w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </label>
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
          >
            Gönder
          </button>
        </form>

        {error && <p className="mt-4 text-red-500">{error}</p>}

        {response && (
          <div className="mt-6 p-4 border-t">
            <h2 className="text-lg font-semibold text-gray-800">Sonuç:</h2>
            <p>
              <strong>Başlık:</strong> {response.data.Title}
            </p>
            <p>
              <strong>URL:</strong>{" "}
              <a
                href={response.data.URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
              >
                {response.data.URL}
              </a>
            </p>
            <p>
              <strong>Süre:</strong> {response.data["Duration (seconds)"]} saniye
            </p>
            <p>
              <strong>Dil:</strong> {response.data.Language}
            </p>
            <p>
              <strong>Özet:</strong> {response.data.Summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
