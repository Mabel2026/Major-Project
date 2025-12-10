import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import whisper
import spacy
import re
from pydub import AudioSegment
from pydub.generators import Sine
import os
import threading

class AudioRedactorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔊 Redactly - Audio Privacy Redactor")
        self.root.geometry("900x750")
        self.root.configure(bg='#1E3A8A')
        self.root.resizable(True, True)
        
        # Modern blue theme colors
        self.colors = {
            'primary': '#1E3A8A',
            'secondary': '#2563EB', 
            'accent': '#3B82F6',
            'light_bg': '#EFF6FF',
            'card_bg': '#FFFFFF',
            'text_primary': '#1E293B',
            'text_secondary': '#64748B',
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'progress': '#3B82F6'
        }
        
        self.models_loaded = False
        self.create_ui()
        self.load_models()
    
    def create_ui(self):
        # Create main container with modern styling
        main_container = tk.Frame(self.root, bg=self.colors['light_bg'], padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with gradient effect simulation
        header_frame = tk.Frame(main_container, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=self.colors['primary'])
        header_content.pack(expand=True, fill=tk.BOTH, padx=30)
        
        # Logo and title
        logo_frame = tk.Frame(header_content, bg=self.colors['primary'])
        logo_frame.pack(side=tk.LEFT)
        
        logo_icon = tk.Label(logo_frame, text="🔊", bg=self.colors['primary'], 
                           fg='white', font=('Arial', 24, 'bold'))
        logo_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = tk.Label(logo_frame, text="Redactly", bg=self.colors['primary'],
                             fg='white', font=('Arial', 24, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(logo_frame, text="Audio Privacy Redactor", 
                                bg=self.colors['primary'], fg='#E0F2FE',
                                font=('Arial', 12))
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator
        self.status_label = tk.Label(header_content, text="Ready", bg=self.colors['primary'],
                                   fg='#E0F2FE', font=('Arial', 10))
        self.status_label.pack(side=tk.RIGHT)
        
        # Main content area
        self.create_upload_section(main_container)
        self.create_analyzing_section(main_container)
        self.create_results_section(main_container)
        
        # Start with upload section
        self.show_upload_section()
    
    def create_upload_section(self, parent):
        self.upload_frame = tk.Frame(parent, bg=self.colors['light_bg'])
        
        # Welcome card
        welcome_card = tk.Frame(self.upload_frame, bg=self.colors['card_bg'], 
                              relief='raised', bd=1, padx=30, pady=30)
        welcome_card.pack(fill=tk.X, pady=10)
        
        welcome_title = tk.Label(welcome_card, text="Upload Audio for Privacy Analysis",
                               bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                               font=('Arial', 20, 'bold'))
        welcome_title.pack(pady=(0, 10))
        
        welcome_text = tk.Label(welcome_card, 
                              text="Protect your sensitive information by automatically detecting and redacting personal data from audio files",
                              bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                              font=('Arial', 11), wraplength=600)
        welcome_text.pack(pady=(0, 20))
        
        # Upload area
        upload_card = tk.Frame(self.upload_frame, bg=self.colors['card_bg'],
                             relief='solid', bd=1, padx=20, pady=30)
        upload_card.pack(fill=tk.X, pady=10)
        
        # Upload box with modern styling
        self.upload_box = tk.Frame(upload_card, bg='#F8FAFC', relief='solid', 
                                 bd=2, highlightbackground='#CBD5E1', highlightthickness=2,
                                 width=400, height=150)
        self.upload_box.pack(pady=20)
        self.upload_box.pack_propagate(False)
        self.upload_box.bind('<Button-1>', self.browse_file)
        
        # Hover effects
        self.upload_box.bind('<Enter>', lambda e: self.upload_box.config(
            highlightbackground=self.colors['accent'], bg='#F1F5F9'))
        self.upload_box.bind('<Leave>', lambda e: self.upload_box.config(
            highlightbackground='#CBD5E1', bg='#F8FAFC'))
        
        upload_content = tk.Frame(self.upload_box, bg=self.upload_box['bg'])
        upload_content.pack(expand=True)
        
        upload_icon = tk.Label(upload_content, text="📁", 
                             bg=self.upload_box['bg'], fg=self.colors['accent'],
                             font=('Arial', 32))
        upload_icon.pack(pady=(10, 5))
        
        upload_title = tk.Label(upload_content, text="Click to Browse Files",
                              bg=self.upload_box['bg'], fg=self.colors['text_primary'],
                              font=('Arial', 14, 'bold'))
        upload_title.pack(pady=5)
        
        upload_subtitle = tk.Label(upload_content, text="or drag and drop your audio file here",
                                 bg=self.upload_box['bg'], fg=self.colors['text_secondary'],
                                 font=('Arial', 10))
        upload_subtitle.pack(pady=5)
        
        # File info
        file_info = tk.Label(upload_card, text="Supported formats: MP3, WAV, M4A, OGG • Max size: 50MB",
                           bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                           font=('Arial', 9))
        file_info.pack(pady=10)
        
        # Analyze button (initially disabled)
        self.analyze_btn = tk.Button(upload_card, text="🔍 Analyze Audio for Privacy Risks",
                                   bg=self.colors['secondary'], fg='white',
                                   font=('Arial', 12, 'bold'),
                                   relief='flat', bd=0, padx=30, pady=12,
                                   cursor='hand2', state='disabled')
        self.analyze_btn.pack(pady=20)
        self.analyze_btn.bind('<Enter>', lambda e: self.analyze_btn.config(bg=self.colors['accent']))
        self.analyze_btn.bind('<Leave>', lambda e: self.analyze_btn.config(bg=self.colors['secondary']))
        self.analyze_btn.config(command=self.start_analysis)
    
    def create_analyzing_section(self, parent):
        self.analyzing_frame = tk.Frame(parent, bg=self.colors['light_bg'])
        
        # Analysis card
        analysis_card = tk.Frame(self.analyzing_frame, bg=self.colors['card_bg'],
                               relief='raised', bd=1, padx=30, pady=40)
        analysis_card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Animated icon
        analyzing_icon = tk.Label(analysis_card, text="🛡️",
                                bg=self.colors['card_bg'], fg=self.colors['accent'],
                                font=('Arial', 48))
        analyzing_icon.pack(pady=(0, 20))
        
        # Title
        title_label = tk.Label(analysis_card, text="Analyzing Your Audio",
                             bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                             font=('Arial', 22, 'bold'))
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(analysis_card,
                                text="Redactly is scanning for sensitive information and privacy risks",
                                bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                                font=('Arial', 12))
        subtitle_label.pack(pady=(0, 30))
        
        # Progress bar with modern styling
        progress_container = tk.Frame(analysis_card, bg='#E2E8F0', height=12, width=400)
        progress_container.pack(pady=20)
        progress_container.pack_propagate(False)
        
        self.progress_bar = tk.Frame(progress_container, bg=self.colors['progress'],
                                   height=12)
        self.progress_bar.pack(anchor='w')
        
        # Progress percentage
        self.progress_label = tk.Label(analysis_card, text="0%",
                                     bg=self.colors['card_bg'], fg=self.colors['text_secondary'],
                                     font=('Arial', 10, 'bold'))
        self.progress_label.pack()
        
        # Steps
        steps_frame = tk.Frame(analysis_card, bg=self.colors['card_bg'])
        steps_frame.pack(pady=30)
        
        self.steps = [
            ("✓", "File Uploaded", "Processing your audio file"),
            ("2", "Transcribing", "Converting speech to text"),
            ("3", "Entity Detection", "Identifying sensitive information"),
            ("4", "Analysis Complete", "Generating privacy report")
        ]
        
        self.step_widgets = []
        for icon, title, description in self.steps:
            step_frame = tk.Frame(steps_frame, bg='#F8FAFC', relief='solid', 
                                bd=1, padx=15, pady=10)
            step_frame.pack(fill=tk.X, pady=5)
            
            # Step icon
            icon_bg = '#E2E8F0' if icon != "✓" else self.colors['success']
            icon_frame = tk.Frame(step_frame, bg=icon_bg, width=24, height=24)
            icon_frame.pack(side=tk.LEFT, padx=(0, 15))
            icon_frame.pack_propagate(False)
            
            icon_label = tk.Label(icon_frame, text=icon, bg=icon_bg, fg=self.colors['text_primary'],
                                font=('Arial', 10, 'bold'))
            icon_label.pack(expand=True)
            
            # Step content
            content_frame = tk.Frame(step_frame, bg=step_frame['bg'])
            content_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            title_label = tk.Label(content_frame, text=title, 
                                 bg=step_frame['bg'], fg=self.colors['text_primary'],
                                 font=('Arial', 11, 'bold'), anchor='w')
            title_label.pack(anchor='w')
            
            desc_label = tk.Label(content_frame, text=description,
                                bg=step_frame['bg'], fg=self.colors['text_secondary'],
                                font=('Arial', 9), anchor='w')
            desc_label.pack(anchor='w')
            
            self.step_widgets.append((step_frame, icon_frame, icon_label))
    
    def create_results_section(self, parent):
        self.results_frame = tk.Frame(parent, bg=self.colors['light_bg'])
        
        # Results header
        header_card = tk.Frame(self.results_frame, bg=self.colors['card_bg'],
                             relief='raised', bd=1, padx=20, pady=15)
        header_card.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(header_card, text="Analysis Complete",
                             bg=self.colors['card_bg'], fg=self.colors['text_primary'],
                             font=('Arial', 18, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        success_label = tk.Label(header_card, text="✓ Privacy assessment finished",
                               bg=self.colors['card_bg'], fg=self.colors['success'],
                               font=('Arial', 10, 'bold'))
        success_label.pack(side=tk.RIGHT)
        
        # Notebook for tabs
        style = ttk.Style()
        style.configure('Blue.TNotebook', background=self.colors['light_bg'])
        style.configure('Blue.TNotebook.Tab', 
                       background='#E2E8F0',
                       foreground=self.colors['text_primary'],
                       padding=[15, 8],
                       font=('Arial', 10, 'bold'))
        style.map('Blue.TNotebook.Tab',
                 background=[('selected', self.colors['secondary'])],
                 foreground=[('selected', 'white')])
        
        notebook = ttk.Notebook(self.results_frame, style='Blue.TNotebook')
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tab 1: Detected Information
        entities_tab = tk.Frame(notebook, bg=self.colors['light_bg'], padx=10, pady=10)
        notebook.add(entities_tab, text="🔍 Detected Information")
        
        entities_title = tk.Label(entities_tab, 
                                text="Sensitive Information Found",
                                bg=self.colors['light_bg'], fg=self.colors['text_primary'],
                                font=('Arial', 14, 'bold'))
        entities_title.pack(anchor='w', pady=(0, 10))
        
        self.entities_text = scrolledtext.ScrolledText(entities_tab, height=12,
                                                     bg='white', fg=self.colors['text_primary'],
                                                     insertbackground=self.colors['text_primary'],
                                                     font=('Arial', 10),
                                                     relief='solid', bd=1)
        self.entities_text.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: Redaction Settings
        settings_tab = tk.Frame(notebook, bg=self.colors['light_bg'], padx=10, pady=10)
        notebook.add(settings_tab, text="⚙️ Redaction Settings")
        
        # Redaction method
        method_frame = tk.Frame(settings_tab, bg=self.colors['light_bg'])
        method_frame.pack(fill=tk.X, pady=10)
        
        method_label = tk.Label(method_frame, text="Redaction Method:",
                              bg=self.colors['light_bg'], fg=self.colors['text_primary'],
                              font=('Arial', 12, 'bold'))
        method_label.pack(anchor='w')
        
        self.redaction_method = tk.StringVar(value="mute")
        
        methods = [
            ("🔇 Mute sensitive words", "mute"),
            ("🔊 Beep (TV-style censorship)", "beep"),
            ("✂️ Trim and remove completely", "trim")
        ]
        
        for text, value in methods:
            rb = tk.Radiobutton(method_frame, text=text, variable=self.redaction_method,
                              value=value, bg=self.colors['light_bg'], fg=self.colors['text_primary'],
                              selectcolor=self.colors['secondary'], font=('Arial', 10))
            rb.pack(anchor='w', pady=5)
        
        # Custom words
        custom_frame = tk.Frame(settings_tab, bg=self.colors['light_bg'])
        custom_frame.pack(fill=tk.X, pady=20)
        
        custom_label = tk.Label(custom_frame, text="Additional Words to Redact:",
                              bg=self.colors['light_bg'], fg=self.colors['text_primary'],
                              font=('Arial', 12, 'bold'))
        custom_label.pack(anchor='w')
        
        custom_help = tk.Label(custom_frame, 
                              text="Enter comma-separated words (e.g., confidential, secret)",
                              bg=self.colors['light_bg'], fg=self.colors['text_secondary'],
                              font=('Arial', 9))
        custom_help.pack(anchor='w', pady=(0, 5))
        
        self.custom_words = tk.StringVar()
        custom_entry = tk.Entry(custom_frame, textvariable=self.custom_words,
                              bg='white', fg=self.colors['text_primary'],
                              insertbackground=self.colors['text_primary'],
                              font=('Arial', 10), width=50)
        custom_entry.pack(fill=tk.X, pady=5)
        
        # Redact button
        self.redact_btn = tk.Button(settings_tab, text="🚀 Apply Redaction",
                                  bg=self.colors['secondary'], fg='white',
                                  font=('Arial', 11, 'bold'),
                                  relief='flat', bd=0, padx=25, pady=10,
                                  cursor='hand2')
        self.redact_btn.pack(pady=20)
        self.redact_btn.bind('<Enter>', lambda e: self.redact_btn.config(bg=self.colors['accent']))
        self.redact_btn.bind('<Leave>', lambda e: self.redact_btn.config(bg=self.colors['secondary']))
        
        # Tab 3: Transcripts
        transcripts_tab = tk.Frame(notebook, bg=self.colors['light_bg'], padx=10, pady=10)
        notebook.add(transcripts_tab, text="📝 Transcripts")
        
        # Original transcript
        original_label = tk.Label(transcripts_tab, text="Original Transcript",
                                bg=self.colors['light_bg'], fg=self.colors['text_primary'],
                                font=('Arial', 12, 'bold'))
        original_label.pack(anchor='w', pady=(0, 5))
        
        self.original_text = scrolledtext.ScrolledText(transcripts_tab, height=6,
                                                     bg='white', fg=self.colors['text_primary'],
                                                     insertbackground=self.colors['text_primary'],
                                                     font=('Arial', 10),
                                                     relief='solid', bd=1)
        self.original_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Redacted transcript
        redacted_label = tk.Label(transcripts_tab, text="Redacted Transcript",
                                bg=self.colors['light_bg'], fg=self.colors['text_primary'],
                                font=('Arial', 12, 'bold'))
        redacted_label.pack(anchor='w', pady=(0, 5))
        
        self.redacted_text = scrolledtext.ScrolledText(transcripts_tab, height=6,
                                                     bg='white', fg=self.colors['text_primary'],
                                                     insertbackground=self.colors['text_primary'],
                                                     font=('Arial', 10),
                                                     relief='solid', bd=1)
        self.redacted_text.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons
        button_frame = tk.Frame(self.results_frame, bg=self.colors['light_bg'], pady=20)
        button_frame.pack(fill=tk.X)
        
        self.download_btn = tk.Button(button_frame, text="📥 Download Redacted Audio",
                                    bg=self.colors['success'], fg='white',
                                    font=('Arial', 11, 'bold'),
                                    relief='flat', bd=0, padx=25, pady=10,
                                    cursor='hand2', state='disabled')
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.new_analysis_btn = tk.Button(button_frame, text="🔄 Analyze Another File",
                                        bg=self.colors['secondary'], fg='white',
                                        font=('Arial', 11, 'bold'),
                                        relief='flat', bd=0, padx=25, pady=10,
                                        cursor='hand2')
        self.new_analysis_btn.pack(side=tk.LEFT)
    
    def show_upload_section(self):
        self.hide_all_sections()
        self.upload_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label.config(text="Ready to analyze")
    
    def show_analyzing_section(self):
        self.hide_all_sections()
        self.analyzing_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label.config(text="Analyzing...")
    
    def show_results_section(self):
        self.hide_all_sections()
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label.config(text="Analysis complete")
    
    def hide_all_sections(self):
        for frame in [self.upload_frame, self.analyzing_frame, self.results_frame]:
            frame.pack_forget()
    
    def browse_file(self, event=None):
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.m4a *.ogg"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path = filename
            self.analyze_btn.config(state='normal', bg=self.colors['success'])
            
            # Update upload box to show selected file
            for widget in self.upload_box.winfo_children():
                widget.destroy()
            
            success_content = tk.Frame(self.upload_box, bg=self.upload_box['bg'])
            success_content.pack(expand=True)
            
            success_icon = tk.Label(success_content, text="✅", 
                                  bg=self.upload_box['bg'], fg=self.colors['success'],
                                  font=('Arial', 32))
            success_icon.pack(pady=(10, 5))
            
            file_name = os.path.basename(filename)
            success_title = tk.Label(success_content, text="File Selected",
                                   bg=self.upload_box['bg'], fg=self.colors['text_primary'],
                                   font=('Arial', 14, 'bold'))
            success_title.pack(pady=5)
            
            success_subtitle = tk.Label(success_content, text=file_name,
                                      bg=self.upload_box['bg'], fg=self.colors['text_secondary'],
                                      font=('Arial', 10))
            success_subtitle.pack(pady=5)
    
    def load_models(self):
        def load_models_thread():
            self.status_label.config(text="Loading AI models...")
            try:
                self.whisper_model = whisper.load_model("base")
                self.nlp = spacy.load("en_core_web_sm")
                self.models_loaded = True
                self.status_label.config(text="Models loaded")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load models: {str(e)}")
        
        threading.Thread(target=load_models_thread, daemon=True).start()
    
    def start_analysis(self):
        if not hasattr(self, 'file_path'):
            messagebox.showerror("Error", "Please select an audio file first.")
            return
        
        if not self.models_loaded:
            messagebox.showerror("Error", "AI models are still loading. Please wait.")
            return
        
        self.show_analyzing_section()
        self.simulate_progress()
        
        # Start actual analysis in background
        threading.Thread(target=self.analyze_audio, daemon=True).start()
    
    def simulate_progress(self):
        def update_progress():
            for i in range(101):
                self.progress_bar.config(width=4 * i)  # 400px width
                self.progress_label.config(text=f"{i}%")
                self.root.update()
                
                # Update steps
                if i >= 25 and len(self.step_widgets) > 1:
                    self.update_step(1, self.colors['accent'])
                if i >= 50 and len(self.step_widgets) > 2:
                    self.update_step(2, self.colors['accent'])
                if i >= 75 and len(self.step_widgets) > 3:
                    self.update_step(3, self.colors['success'])
                
                self.root.after(20)  # Faster animation
        
        threading.Thread(target=update_progress, daemon=True).start()
    
    def update_step(self, index, color):
        self.step_widgets[index][1].config(bg=color)
        self.step_widgets[index][2].config(bg=color)
        if color == self.colors['success']:
            self.step_widgets[index][2].config(text="✓")
    
    def analyze_audio(self):
        try:
            # Transcribe audio
            result = self.whisper_model.transcribe(self.file_path, word_timestamps=True)
            original_text = result["text"]
            
            # Extract entities
            doc = self.nlp(original_text)
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)
            
            # Store data
            self.original_text_data = original_text
            self.entities_data = entities
            self.word_list_data = []
            
            for seg in result['segments']:
                if 'words' in seg:
                    for w in seg['words']:
                        self.word_list_data.append({
                            'word': w['word'].strip(), 
                            'start': w['start'], 
                            'end': w['end']
                        })
            
            # Update UI in main thread
            self.root.after(0, self.show_results, original_text, entities)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {str(e)}"))
            self.root.after(0, self.show_upload_section)
    
    def show_results(self, original_text, entities):
        self.show_results_section()
        
        # Update entities display
        entities_text = "The following sensitive information was detected:\n\n"
        entity_types = {
            'PERSON': '👤 People Names',
            'GPE': '🏙️ Locations', 
            'ORG': '🏢 Organizations',
            'DATE': '📅 Dates & Times',
            'MONEY': '💰 Monetary Values'
        }
        
        detected_any = False
        for entity_type, items in entities.items():
            if items:
                detected_any = True
                display_name = entity_types.get(entity_type, entity_type)
                entities_text += f"{display_name}:\n"
                for item in items:
                    entities_text += f"  • {item}\n"
                entities_text += "\n"
        
        if not detected_any:
            entities_text = "No sensitive information was automatically detected.\nYou can add custom words to redact in the settings tab."
        
        self.entities_text.delete(1.0, tk.END)
        self.entities_text.insert(1.0, entities_text)
        
        # Update original transcript
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(1.0, original_text)
        
        # Configure buttons
        self.redact_btn.config(command=self.apply_redaction)
        self.new_analysis_btn.config(command=self.show_upload_section)
        
        # Clear redacted transcript and disable download
        self.redacted_text.delete(1.0, tk.END)
        self.download_btn.config(state='disabled')
    
    def apply_redaction(self):
        if not hasattr(self, 'original_text_data'):
            messagebox.showerror("Error", "No analysis data available.")
            return
        
        self.show_analyzing_section()
        self.progress_bar.config(width=0)
        self.progress_label.config(text="0%")
        
        threading.Thread(target=self.redact_audio, daemon=True).start()
    
    def redact_audio(self):
        try:
            # Get words to redact
            words_to_redact = []
            sensitive_entities = ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY']
            
            for entity_type in sensitive_entities:
                if entity_type in self.entities_data:
                    for entity in self.entities_data[entity_type]:
                        words = entity.split()
                        words_to_redact.extend(words)
            
            # Add custom words
            if self.custom_words.get():
                custom_list = [word.strip() for word in self.custom_words.get().split(',') if word.strip()]
                words_to_redact.extend(custom_list)
            
            words_to_redact = list(set([word.strip() for word in words_to_redact if word.strip()]))
            
            # Find sensitive segments
            sensitive_segments = []
            for word_info in self.word_list_data:
                current_word = word_info['word'].lower().strip(' ,.!?;:"')
                for target_word in words_to_redact:
                    target_clean = target_word.lower().strip(' ,.!?;:"')
                    if (target_clean == current_word or 
                        (len(target_clean) > 2 and target_clean in current_word)):
                        sensitive_segments.append((word_info['start'], word_info['end']))
            
            # Apply buffers
            buffered_segments = [(max(0, start - 0.1), end + 0.1) for start, end in sensitive_segments]
            
            # Apply redaction
            audio = AudioSegment.from_file(self.file_path)
            method = self.redaction_method.get()
            
            if method == "mute":
                redacted_audio = audio
                for start, end in buffered_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    silence = AudioSegment.silent(duration=(end_ms - start_ms))
                    redacted_audio = redacted_audio[:start_ms] + silence + redacted_audio[end_ms:]
            
            elif method == "trim":
                redacted_audio = AudioSegment.empty()
                prev_end = 0
                for start, end in buffered_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    redacted_audio += audio[prev_end:start_ms]
                    prev_end = end_ms
                redacted_audio += audio[prev_end:]
            
            elif method == "beep":
                redacted_audio = audio
                for start, end in buffered_segments:
                    start_ms = max(0, int(start * 1000))
                    end_ms = min(len(audio), int(end * 1000))
                    beep_duration = end_ms - start_ms
                    if beep_duration > 0:
                        beep = Sine(1000).to_audio_segment(duration=beep_duration)
                        beep = beep.apply_gain(-10)
                        redacted_audio = redacted_audio[:start_ms] + beep + redacted_audio[end_ms:]
            
            # Save file
            original_name = os.path.splitext(os.path.basename(self.file_path))[0]
            self.output_filename = f"redacted_{original_name}_{method}.wav"
            redacted_audio.export(self.output_filename, format="wav")
            
            # Create redacted transcript
            redacted_transcript = self.original_text_data
            for word in words_to_redact:
                redacted_transcript = re.sub(r'\b' + re.escape(word) + r'\b', '[REDACTED]', redacted_transcript, flags=re.IGNORECASE)
            
            self.root.after(0, self.redaction_complete, redacted_transcript)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Redaction failed: {str(e)}"))
            self.root.after(0, self.show_results_section)
    
    def redaction_complete(self, redacted_transcript):
        self.show_results_section()
        
        # Update redacted transcript
        self.redacted_text.delete(1.0, tk.END)
        self.redacted_text.insert(1.0, redacted_transcript)
        
        # Enable download button
        self.download_btn.config(state='normal', command=self.download_audio)
        
        messagebox.showinfo("Success", f"Redaction complete!\n\nFile saved as: {self.output_filename}")
    
    def download_audio(self):
        if hasattr(self, 'output_filename') and os.path.exists(self.output_filename):
            file_path = os.path.abspath(self.output_filename)
            messagebox.showinfo("Download Ready", 
                              f"Redacted audio saved successfully!\n\n"
                              f"File: {self.output_filename}\n"
                              f"Location: {file_path}")
        else:
            messagebox.showerror("Error", "Redacted file not found.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRedactorApp(root)
    root.mainloop()