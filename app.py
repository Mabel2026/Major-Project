from flask import Flask, request, jsonify, render_template
import os
import tempfile
import traceback

app = Flask(__name__)

print("🔊 Starting Audio Redactor Server...")

# Initialize redactor (but don't crash if it fails)
redactor = None
try:
    from universal_redact import AudioNERRedactor
    print("🔄 Attempting to initialize AudioNERRedactor...")
    redactor = AudioNERRedactor()
    print("✅ AudioNERRedactor initialized successfully!")
except Exception as e:
    print(f"❌ AudioNERRedactor initialization failed: {e}")
    print("⚠️  Server will run in limited mode")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return jsonify({'status': 'success', 'message': 'Server is running!'})

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy', 
        'redactor_initialized': redactor is not None
    })

@app.route('/routes')
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
    return jsonify({'routes': routes})

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    print("🎵 /analyze POST endpoint called!")
    
    try:
        # Check if file was uploaded
        if 'audio_file' not in request.files:
            print("❌ No audio_file in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['audio_file']
        print(f"📁 Received file: {file.filename}")
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # For now, return a simple success response
        return jsonify({
            'status': 'success',
            'message': 'File received successfully!',
            'filename': file.filename,
            'file_size': len(file.read()),
            'issues': [
                {
                    'id': 1,
                    'type': 'Test Entity',
                    'word': 'example',
                    'start': '00:01',
                    'end': '00:02'
                }
            ]
        })
        
    except Exception as e:
        print(f"❌ Error in analyze_audio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/simple_analyze', methods=['POST'])
def simple_analyze():
    print("🎵 /simple_analyze POST endpoint called!")
    return jsonify({
        'status': 'success', 
        'message': 'Simple analyze works!'
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Flask Audio Redactor Server Starting...")
    print("🌐 http://localhost:5000")
    print("📋 Available endpoints:")
    print("   GET  /              - Main page")
    print("   GET  /test          - Test endpoint") 
    print("   GET  /health        - Health check")
    print("   GET  /routes        - List all routes")
    print("   POST /analyze       - Analyze audio")
    print("   POST /simple_analyze - Simple test")
    print("=" * 50)
    
    app.run(debug=True, port=5000, host='0.0.0.0')