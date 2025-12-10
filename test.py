from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask is working!"

@app.route('/analyze', methods=['POST'])
def analyze():
    print("✅ /analyze endpoint called with POST!")
    return jsonify({"status": "success", "message": "POST to /analyze works!"})

@app.route('/test')
def test():
    return jsonify({"status": "success", "message": "GET /test works!"})

if __name__ == '__main__':
    print("🚀 Starting simple Flask test on port 5000...")
    print("📝 Testing:")
    print("   GET  http://localhost:5000/test")
    print("   POST http://localhost:5000/analyze")
    app.run(debug=True, port=5000)