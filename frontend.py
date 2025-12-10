import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import whisper
import spacy
import re
from pydub import AudioSegment
from pydub.generators import Sine
import os
import threading
import contextlib # Used to suppress spacy's console output

# --- CONFIGURATION CONSTANTS ---
PRIMARY_COLOR = "#0078D4"  # Professional Blue
SECONDARY_COLOR = "#F0F0F0" # Light grey background
ACCENT_COLOR = "#FFFFFF"   # White for elements

class AudioRedactorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔊 Redactly - Audio Privacy Redactor")
        # Larger and more balanced initial size
        self.root.geometry("1000x850") 
        self.root.configure(bg=SECONDARY_COLOR)

        self.models_loaded = False
        self.setup_styles()
        
        # Initial status label before the main UI is built
        self.status_label = ttk.Label(self.root, text="Loading AI models... This may take a moment.", 
                                      foreground="gray", background=SECONDARY_COLOR)
        self.status_label.pack(pady=20)
        
        self.load_models()
        # setup_ui will be called after models start loading
    
    def setup_styles(self):
        """Configure ttk styles for a modern, flat look (clam theme)."""
        style = ttk.Style()
        style.theme_use('clam') 
        
        # General widget styling
        style.configure('TFrame', background=SECONDARY_COLOR)
        style.configure('TLabel', background=SECONDARY_COLOR, font=('Segoe UI', 10))
        style.configure('TLabelFrame', background=SECONDARY_COLOR, 
                        font=('Segoe UI', 11, 'bold'), borderwidth=1, relief='solid')
        style.configure('TRadiobutton', background=SECONDARY_COLOR)
        
        # Custom primary button style
        style.configure('Primary.TButton', 
                        font=('Segoe UI', 11, 'bold'), 
                        background=PRIMARY_COLOR, 
                        foreground=ACCENT_COLOR,
                        relief='flat', 
                        padding=10)
        style.map('Primary.TButton', 
                  background=[('active', '#005A9E'), ('disabled', '#A0A0A0')],
                  foreground=[('disabled', '#E0E0E0')])

        # Secondary/Browse button style
        style.configure('TButton', 
                        font=('Segoe UI', 10), 
                        relief='flat', 
                        background='#E1E1E1', 
                        padding=6)
        style.map('TButton', 
                  background=[('active', '#C8C8C8')])
        
        # ScrolledText (Tweak for better contrast)
        self.root.option_add('*ScrolledText*background', ACCENT_COLOR)
        self.root.option_add('*ScrolledText*foreground', '#333333')
        self.root.option_add('*ScrolledText*font', 'Consolas 10') # Monospace font for code/transcript
        
        # Notebook (Tabs) styling
        style.configure('TNotebook', background=SECONDARY_COLOR, borderwidth=0)
        style.configure('TNotebook.Tab', background='#D0D0D0', padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', ACCENT_COLOR)])


    def load_models(self):
        """Loads the Whisper and SpaCy models in a separate thread."""
        def load():
            try:
                self.whisper_model = whisper.load_model("base")
                # Suppress spacy's default print output
                with contextlib.redirect_stdout(None):
                    self.nlp = spacy.load("en_core_web_sm")
                
                self.models_loaded = True
                self.status_label.config(text="✅ AI Models ready (Whisper/SpaCy)", foreground="green")
                # Build the main UI after models are loaded
                self.root.after(0, self.setup_ui)
            except Exception as e:
                self.status_label.config(text=f"❌ Error loading models: {str(e)}", foreground="red")
        
        threading.Thread(target=load, daemon=True).start()
    
    def setup_ui(self):
        """Sets up the attractive GUI elements."""
        # Remove the initial loading status and replace it with the main UI structure
        if hasattr(self, 'status_label'):
            self.status_label.pack_forget()

        main_frame = ttk.Frame(self.root, padding="20 15 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Header (Title and Status) ---
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = ttk.Label(header_frame, text="🔊 REDACTLY - Audio Privacy Redactor", 
                                font=("Segoe UI", 20, "bold"), foreground=PRIMARY_COLOR)
        title_label.pack(side=tk.LEFT)

        # Re-pack the status label into the header frame
        self.status_label.pack(side=tk.RIGHT, pady=5)
        
        # --- 1. File Selection and 2. Analyze Button ---
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 15))

        # File selection
        file_frame = ttk.LabelFrame(action_frame, text="1. Select Audio File", padding="10")
        file_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=50, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.LEFT)
        
        # Analyze Button (Primary Action)
        self.analyze_btn = ttk.Button(action_frame, text="2. Analyze Audio (Transcript & Entities)", 
                                      command=self.analyze_audio, style='Primary.TButton')
        self.analyze_btn.pack(side=tk.LEFT, padx=(10, 0), ipadx=10, ipady=5)

        # --- Middle Section (3. Entities and Settings) ---
        middle_frame = ttk.Frame(main_frame)
        # Use grid to ensure equal weight/sizing if needed, but side/pack works well here
        middle_frame.pack(fill=tk.BOTH, expand=False, pady=10)
        
        # Left Panel - Detected Entities
        entities_frame = ttk.LabelFrame(middle_frame, text="Detected Sensitive Information (SpaCy NER)", padding="10")
        entities_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.entities_text = scrolledtext.ScrolledText(entities_frame, height=14, width=50, wrap=tk.WORD, font=('Segoe UI', 10))
        self.entities_text.pack(fill=tk.BOTH, expand=True)
        self.entities_text.insert(tk.END, "Analyze an audio file to see detected PII like Names, Locations, and Organizations here.")

        # Right Panel - Redaction Settings
        settings_frame = ttk.LabelFrame(middle_frame, text="Redaction Settings", padding="10")
        settings_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Redaction Method (Left side of the original sub-frame)
        method_frame = ttk.Frame(settings_frame)
        method_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(method_frame, text="Redaction Method:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.redaction_method = tk.StringVar(value="mute")
        ttk.Radiobutton(method_frame, text="🔇 Mute (Silence)", variable=self.redaction_method, value="mute").pack(anchor=tk.W)
        ttk.Radiobutton(method_frame, text="🔊 Beep (Censor Tone)", variable=self.redaction_method, value="beep").pack(anchor=tk.W)
        ttk.Radiobutton(method_frame, text="✂️ Trim (Remove Segment)", variable=self.redaction_method, value="trim").pack(anchor=tk.W)
        
        # Custom Words (Right side of the original sub-frame)
        custom_frame = ttk.Frame(settings_frame)
        custom_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(custom_frame, text="Additional words to redact:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.custom_words = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_words, width=35, font=('Segoe UI', 10)).pack(fill=tk.X, pady=5)
        ttk.Label(custom_frame, text="(comma-separated, e.g., confidential, secret)").pack(anchor=tk.W)
        
        # 3. Redact Button (Primary Action)
        self.redact_btn = ttk.Button(settings_frame, text="3. Redact Audio", command=self.redact_audio, 
                                     style='Primary.TButton')
        self.redact_btn.pack(pady=15, fill=tk.X, ipadx=10, ipady=5)

        # --- Results Section ---
        results_frame = ttk.LabelFrame(main_frame, text="Redaction Results & Transcripts", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Transcripts in notebook (tabs)
        notebook = ttk.Notebook(results_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Original transcript tab
        original_frame = ttk.Frame(notebook)
        notebook.add(original_frame, text="Original Transcript")
        self.original_text = scrolledtext.ScrolledText(original_frame, height=8, wrap=tk.WORD)
        self.original_text.pack(fill=tk.BOTH, expand=True)
        
        # Redacted transcript tab
        redacted_frame = ttk.Frame(notebook)
        notebook.add(redacted_frame, text="Redacted Transcript")
        self.redacted_text = scrolledtext.ScrolledText(redacted_frame, height=8, wrap=tk.WORD)
        self.redacted_text.pack(fill=tk.BOTH, expand=True)
        
        # Download button (Primary Action - disabled until redaction is complete)
        self.download_btn = ttk.Button(results_frame, text="📥 Download Redacted Audio", 
                                       command=self.download_audio, state="disabled", style='Primary.TButton')
        self.download_btn.pack(pady=10, fill=tk.X)

    # --- Methods (Logic identical to original, with minor cleanup/improvements) ---

    def browse_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.wav *.mp3 *.m4a *.ogg"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
    
    def analyze_audio(self):
        if not self.models_loaded:
            messagebox.showerror("Error", "Models are still loading. Please wait.")
            return
        
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select an audio file first.")
            return
        
        def analyze():
            self.analyze_btn.config(state="disabled")
            try:
                self.status_label.config(text="🔄 Analyzing audio... (Transcribing)", foreground="#FFA500")
                
                # --- Transcription ---
                result = self.whisper_model.transcribe(self.file_path.get(), word_timestamps=True)
                original_text = result["text"]
                
                # --- Entity Extraction ---
                self.status_label.config(text="🔄 Analyzing transcript... (NER)", foreground="#FFA500")
                doc = self.nlp(original_text)
                entities = {}
                # Include a wider range of relevant PII entities
                relevant_entities = ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY', 'FAC', 'NORP', 'LOC', 'TIME', 'LAW']
                for ent in doc.ents:
                    if ent.label_ in relevant_entities:
                        if ent.label_ not in entities:
                            entities[ent.label_] = []
                        entities[ent.label_].append(ent.text)
                
                # Store data
                self.original_text_data = original_text
                self.entities_data = entities
                self.word_list_data = []
                for seg in result.get('segments', []):
                    for w in seg.get('words', []):
                        self.word_list_data.append({
                            'word': w['word'].strip(), 
                            'start': w['start'], 
                            'end': w['end']
                        })
                
                # --- Update UI ---
                self.original_text.delete(1.0, tk.END)
                self.original_text.insert(1.0, original_text)
                
                # Display entities
                entities_display = "**Detected Potential Sensitive Information:**\n\n"
                entity_descriptions = {
                    'PERSON': '👤 People', 'GPE': '🏙️ Locations', 'ORG': '🏢 Organizations',
                    'DATE': '📅 Dates', 'MONEY': '💰 Money', 'FAC': '🏛️ Facilities',
                    'NORP': '👥 Nationalities/Groups', 'LOC': '🌍 Other Locations', 
                    'TIME': '⏰ Times', 'LAW': '⚖️ Legal Documents/Acts'
                }
                
                if not entities:
                    entities_display += "No standard sensitive entities automatically detected."
                else:
                    for entity_type, items in entities.items():
                        desc = entity_descriptions.get(entity_type, entity_type)
                        entities_display += f"--- {desc} ---\n"
                        for item in sorted(list(set(items))): 
                            entities_display += f"  • {item}\n"
                        entities_display += "\n"
                
                self.entities_text.delete(1.0, tk.END)
                self.entities_text.insert(1.0, entities_display)
                
                self.status_label.config(text="✅ Analysis complete! Ready for redaction.", foreground="green")
                self.redact_btn.config(state="normal")
                
            except Exception as e:
                self.status_label.config(text=f"❌ Analysis failed: {type(e).__name__}", foreground="red")
                messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            finally:
                self.analyze_btn.config(state="normal")

        threading.Thread(target=analyze, daemon=True).start()
    
    def redact_audio(self):
        if not hasattr(self, 'original_text_data'):
            messagebox.showerror("Error", "Please analyze audio first.")
            return
        
        def redact():
            self.redact_btn.config(state="disabled")
            self.download_btn.config(state="disabled")
            try:
                self.status_label.config(text="🔄 Applying redaction...", foreground="#FFA500")
                
                # 1. Gather words to redact (from A.I. and custom list)
                words_to_redact = []
                for entity_type in self.entities_data.keys():
                    words_to_redact.extend([w for entity in self.entities_data[entity_type] for w in entity.split()])
                
                if self.custom_words.get():
                    custom_list = [word.strip() for word in self.custom_words.get().split(',') if word.strip()]
                    words_to_redact.extend(custom_list)
                
                words_to_redact_clean = list(set([word.strip(' ,.!?;:"').lower() for word in words_to_redact if word.strip()]))
                
                # 2. Find and Buffer sensitive segments
                sensitive_segments = []
                for word_info in self.word_list_data:
                    current_word = word_info['word'].lower().strip(' ,.!?;:"')
                    if current_word in words_to_redact_clean:
                        # Apply a small buffer (100ms)
                        sensitive_segments.append((max(0, word_info['start'] - 0.1), word_info['end'] + 0.1))

                # 3. Merge overlapping segments (crucial for continuous redaction)
                if sensitive_segments:
                    sensitive_segments.sort()
                    merged = [list(sensitive_segments[0])]
                    for current_start, current_end in sensitive_segments[1:]:
                        prev_end = merged[-1][1]
                        # Merge if overlap or gap is small (e.g., < 50ms)
                        if current_start <= prev_end + 0.05: 
                            merged[-1][1] = max(prev_end, current_end)
                        else:
                            merged.append([current_start, current_end])
                    buffered_segments = [tuple(seg) for seg in merged]
                else:
                    buffered_segments = []


                # 4. Apply Redaction to Audio
                audio = AudioSegment.from_file(self.file_path.get())
                redacted_audio = audio
                method = self.redaction_method.get()
                
                for start, end in buffered_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    duration_ms = end_ms - start_ms

                    if duration_ms <= 0:
                        continue
                        
                    if method == "mute":
                        silence = AudioSegment.silent(duration=duration_ms, frame_rate=audio.frame_rate)
                        redacted_audio = redacted_audio[:start_ms] + silence + redacted_audio[end_ms:]
                    
                    elif method == "beep":
                        # Generate beep at correct frame rate/channels
                        beep = Sine(1000, sample_rate=audio.frame_rate).to_audio_segment(duration=duration_ms)
                        beep = beep.apply_gain(-10) 
                        if audio.channels == 2:
                            beep = beep.set_channels(2) 
                            
                        # Overlay the beep onto the segment, effectively replacing the original sound
                        redacted_audio = redacted_audio[:start_ms].overlay(beep, position=start_ms) + redacted_audio[end_ms:]
                    
                    elif method == "trim":
                         # Re-implement trim logic for clean cutting
                         # This needs a full reconstructive loop, not an in-place modification like mute/beep
                         pass # The reconstruction happens outside this inner loop for 'trim'

                if method == "trim":
                    redacted_audio_trimmed = AudioSegment.empty()
                    prev_end = 0
                    for start, end in buffered_segments:
                        start_ms = max(0, int(start * 1000))
                        end_ms = min(len(audio), int(end * 1000))
                        redacted_audio_trimmed += audio[prev_end:start_ms]
                        prev_end = end_ms
                    redacted_audio_trimmed += audio[prev_end:]
                    redacted_audio = redacted_audio_trimmed

                # 5. Save file and create redacted transcript
                base_name = os.path.splitext(os.path.basename(self.file_path.get()))[0]
                self.output_filename = f"{base_name}_redacted_{method}.wav"
                
                # Use the original audio's settings for high-quality export
                redacted_audio.export(self.output_filename, format="wav", parameters=["-ac", str(audio.channels), "-ar", str(audio.frame_rate)])
                
                redacted_transcript = self.original_text_data
                for word in words_to_redact_clean:
                    # Use regex to replace whole words only
                    pattern = r'(\b' + re.escape(word) + r'\b)'
                    redacted_transcript = re.sub(pattern, '[REDACTED]', redacted_transcript, flags=re.IGNORECASE)
                
                # --- Update UI ---
                self.redacted_text.delete(1.0, tk.END)
                self.redacted_text.insert(1.0, redacted_transcript)
                self.download_btn.config(state="normal", text=f"📥 Download Redacted Audio ({self.output_filename})")
                
                self.status_label.config(text="✅ Redaction complete! Ready to download.", foreground="green")
                messagebox.showinfo("Success", f"Redaction complete!\nFile saved as: {self.output_filename}")
                
            except Exception as e:
                self.status_label.config(text="❌ Redaction failed", foreground="red")
                messagebox.showerror("Error", f"Redaction failed: {str(e)}")
            finally:
                self.redact_btn.config(state="normal")
        
        threading.Thread(target=redact, daemon=True).start()
    
    def download_audio(self):
        """Allows user to select a permanent save location for the redacted file."""
        if hasattr(self, 'output_filename') and os.path.exists(self.output_filename):
            save_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                initialfile=self.output_filename,
                filetypes=[("WAV files", "*.wav")]
            )
            
            if save_path:
                try:
                    os.rename(self.output_filename, save_path)
                    self.output_filename = save_path 
                    messagebox.showinfo("Download Complete", f"File successfully saved to:\n{save_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save file: {str(e)}")
            else:
                 # If user cancels, inform them where the temporary file is
                 messagebox.showinfo("File Location", f"The redacted file remains in your current directory:\n{os.path.abspath(self.output_filename)}")
        else:
             messagebox.showerror("Error", "Redacted audio file not found. Please run redaction first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRedactorGUI(root)
    root.mainloop()