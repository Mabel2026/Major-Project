import streamlit as st
import whisper
import spacy
import re
from pydub import AudioSegment
from pydub.generators import Sine
import os
import tempfile
import time

# Set page config
st.set_page_config(
    page_title="Redactly - Audio Privacy Redactor",
    page_icon="🔊",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3B82F6;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D1FAE5;
        border: 1px solid #10B981;
        color: #065F46;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #DBEAFE;
        border: 1px solid #3B82F6;
        color: #1E40AF;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FEF3C7;
        border: 1px solid #F59E0B;
        color: #92400E;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border: 1px solid #E5E7EB;
    }
    .step-number {
        background-color: #3B82F6;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class AudioRedactor:
    def __init__(self):
        # Initialize models in session state to avoid reloading
        if 'models_loaded' not in st.session_state:
            st.session_state.models_loaded = False
            st.session_state.whisper_model = None
            st.session_state.nlp = None
            
    def load_models(self):
        """Load AI models with progress indicators"""
        if not st.session_state.models_loaded:
            with st.spinner("🔄 Loading AI models... This may take a moment."):
                try:
                    st.session_state.whisper_model = whisper.load_model("base")
                    st.session_state.nlp = spacy.load("en_core_web_sm")
                    st.session_state.models_loaded = True
                    st.success("✅ Models loaded successfully!")
                except Exception as e:
                    st.error(f"❌ Error loading models: {str(e)}")
                    return False
        return True
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio and get word timestamps"""
        with st.spinner("🔄 Transcribing audio..."):
            try:
                result = st.session_state.whisper_model.transcribe(audio_file, word_timestamps=True)
                return result
            except Exception as e:
                st.error(f"❌ Transcription failed: {str(e)}")
                return None
    
    def extract_entities(self, text):
        """Extract named entities from text"""
        doc = st.session_state.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        return entities
    
    def apply_redaction(self, audio_file, sensitive_segments, method="mute"):
        """Apply redaction to audio file"""
        try:
            audio = AudioSegment.from_file(audio_file)
            
            if method == "mute":
                redacted_audio = audio
                for start, end in sensitive_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    silence = AudioSegment.silent(duration=(end_ms - start_ms))
                    redacted_audio = redacted_audio[:start_ms] + silence + redacted_audio[end_ms:]
            
            elif method == "trim":
                redacted_audio = AudioSegment.empty()
                prev_end = 0
                for start, end in sensitive_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    redacted_audio += audio[prev_end:start_ms]
                    prev_end = end_ms
                redacted_audio += audio[prev_end:]
            
            elif method == "beep":
                redacted_audio = audio
                for start, end in sensitive_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    beep_duration = end_ms - start_ms
                    if beep_duration > 0:
                        beep = Sine(1000).to_audio_segment(duration=beep_duration)
                        beep = beep.apply_gain(-10)
                        redacted_audio = redacted_audio[:start_ms] + beep + redacted_audio[end_ms:]
            
            return redacted_audio
            
        except Exception as e:
            st.error(f"❌ Redaction failed: {str(e)}")
            return None

def main():
    # Initialize redactor
    redactor = AudioRedactor()
    
    # Header
    st.markdown('<div class="main-header">🔊 Redactly - Audio Privacy Redactor</div>', unsafe_allow_html=True)
    
    # Load models
    if not redactor.load_models():
        return
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("ℹ️ How to Use")
        st.markdown("""
        1. **Upload** an audio file
        2. **Analyze** for sensitive information  
        3. **Configure** redaction settings
        4. **Apply** redaction
        5. **Download** redacted audio
        
        **Auto-detects:**
        - 👤 Names
        - 🏙️ Locations
        - 🏢 Organizations  
        - 📅 Dates
        - 💰 Monetary values
        """)
        
        st.header("⚙️ Supported Formats")
        st.markdown("""
        - MP3
        - WAV  
        - M4A
        - OGG
        - and more...
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-header">📁 1. Upload Audio</div>', unsafe_allow_html=True)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'm4a', 'ogg'],
            help="Select an audio file to analyze for sensitive information"
        )
        
        if uploaded_file is not None:
            # Display file info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / (1024*1024):.2f} MB",
                "File type": uploaded_file.type
            }
            
            st.markdown("**File Details:**")
            for key, value in file_details.items():
                st.write(f"- {key}: {value}")
            
            # Play audio
            st.audio(uploaded_file, format='audio/wav')
            
            # Save uploaded file to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                st.session_state.audio_path = tmp_file.name
                st.session_state.uploaded_filename = uploaded_file.name
    
    with col2:
        st.markdown('<div class="section-header">🔍 2. Analyze & Configure</div>', unsafe_allow_html=True)
        
        if 'audio_path' in st.session_state:
            # Analyze button
            if st.button("🔍 Analyze Audio", type="primary", use_container_width=True):
                with st.spinner("Analyzing audio content..."):
                    # Transcribe audio
                    result = redactor.transcribe_audio(st.session_state.audio_path)
                    
                    if result:
                        original_text = result["text"]
                        st.session_state.original_text = original_text
                        
                        # Extract entities
                        entities = redactor.extract_entities(original_text)
                        st.session_state.entities = entities
                        
                        # Store word list for redaction
                        word_list = []
                        for seg in result['segments']:
                            if 'words' in seg:
                                for w in seg['words']:
                                    word_list.append({
                                        'word': w['word'].strip(), 
                                        'start': w['start'], 
                                        'end': w['end']
                                    })
                        st.session_state.word_list = word_list
                        
                        st.success("✅ Analysis complete!")
            
            # Show analysis results if available
            if 'entities' in st.session_state:
                st.markdown("**Detected Sensitive Information:**")
                
                entity_descriptions = {
                    'PERSON': '👤 People',
                    'GPE': '🏙️ Locations', 
                    'ORG': '🏢 Organizations',
                    'DATE': '📅 Dates',
                    'MONEY': '💰 Money',
                    'FAC': '🏛️ Facilities'
                }
                
                detected_any = False
                for entity_type, items in st.session_state.entities.items():
                    desc = entity_descriptions.get(entity_type, entity_type)
                    if items:
                        detected_any = True
                        with st.expander(f"{desc} ({len(items)} found)"):
                            for item in items:
                                st.write(f"• {item}")
                
                if not detected_any:
                    st.info("No sensitive information detected automatically.")
                
                # Redaction settings
                st.markdown("**Redaction Settings:**")
                
                # Method selection
                redaction_method = st.radio(
                    "Redaction Method:",
                    ["mute", "beep", "trim"],
                    format_func=lambda x: {
                        "mute": "🔇 Mute (replace with silence)",
                        "beep": "🔊 Beep (TV-style censorship)", 
                        "trim": "✂️ Trim (remove completely)"
                    }[x]
                )
                
                # Custom words
                custom_words = st.text_input(
                    "Additional words to redact:",
                    placeholder="confidential, secret, project-alpha",
                    help="Enter comma-separated words"
                )
                
                # Store settings
                st.session_state.redaction_method = redaction_method
                st.session_state.custom_words = custom_words
                
                # Redact button
                if st.button("🚀 Apply Redaction", type="primary", use_container_width=True):
                    with st.spinner("Applying redaction..."):
                        # Get words to redact
                        words_to_redact = []
                        for entity_type in ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY']:
                            if entity_type in st.session_state.entities:
                                for entity in st.session_state.entities[entity_type]:
                                    words = entity.split()
                                    words_to_redact.extend(words)
                        
                        # Add custom words
                        if st.session_state.custom_words:
                            custom_list = [word.strip() for word in st.session_state.custom_words.split(',') if word.strip()]
                            words_to_redact.extend(custom_list)
                        
                        words_to_redact = list(set([word.strip() for word in words_to_redact if word.strip()]))
                        
                        # Find sensitive segments
                        sensitive_segments = []
                        for word_info in st.session_state.word_list:
                            current_word = word_info['word'].lower().strip(' ,.!?;:"')
                            for target_word in words_to_redact:
                                target_clean = target_word.lower().strip(' ,.!?;:"')
                                if (target_clean == current_word or 
                                    (len(target_clean) > 2 and target_clean in current_word)):
                                    sensitive_segments.append((word_info['start'], word_info['end']))
                        
                        # Apply buffers
                        buffered_segments = [(max(0, start - 0.1), end + 0.1) for start, end in sensitive_segments]
                        
                        # Apply redaction
                        redacted_audio = redactor.apply_redaction(
                            st.session_state.audio_path,
                            buffered_segments,
                            st.session_state.redaction_method
                        )
                        
                        if redacted_audio:
                            # Save redacted file
                            original_name = os.path.splitext(st.session_state.uploaded_filename)[0]
                            output_filename = f"redacted_{original_name}_{st.session_state.redaction_method}.wav"
                            redacted_audio.export(output_filename, format="wav")
                            
                            # Create redacted transcript
                            redacted_text = st.session_state.original_text
                            for word in words_to_redact:
                                redacted_text = re.sub(r'\b' + re.escape(word) + r'\b', '[REDACTED]', redacted_text, flags=re.IGNORECASE)
                            
                            st.session_state.redacted_audio_path = output_filename
                            st.session_state.redacted_text = redacted_text
                            st.session_state.redaction_complete = True
                            
                            st.success("✅ Redaction complete!")
    
    # Results section
    if 'redaction_complete' in st.session_state and st.session_state.redaction_complete:
        st.markdown("---")
        st.markdown('<div class="section-header">📊 3. Results & Download</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Original Transcript:**")
            st.text_area("", st.session_state.original_text, height=200, key="original_transcript", label_visibility="collapsed")
        
        with col2:
            st.markdown("**Redacted Transcript:**")
            st.text_area("", st.session_state.redacted_text, height=200, key="redacted_transcript", label_visibility="collapsed")
        
        # Download section
        st.markdown("**Download Redacted Audio:**")
        
        if os.path.exists(st.session_state.redacted_audio_path):
            with open(st.session_state.redacted_audio_path, "rb") as file:
                st.download_button(
                    label="📥 Download Redacted Audio",
                    data=file,
                    file_name=st.session_state.redacted_audio_path,
                    mime="audio/wav",
                    type="primary",
                    use_container_width=True
                )
            
            # Play redacted audio
            st.audio(st.session_state.redacted_audio_path, format='audio/wav')
            
            st.info(f"Redacted audio saved as: `{st.session_state.redacted_audio_path}`")
        
        # New analysis button
        if st.button("🔄 Analyze Another File", use_container_width=True):
            # Clear session state
            for key in ['audio_path', 'original_text', 'entities', 'word_list', 
                       'redacted_audio_path', 'redacted_text', 'redaction_complete']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Initial instructions
    elif 'audio_path' not in st.session_state:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📁 Upload")
            st.markdown("Select an audio file from your device")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🔍 Analyze")
            st.markdown("Detect sensitive information automatically")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 🚀 Redact")
            st.markdown("Apply privacy protection to your audio")
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()