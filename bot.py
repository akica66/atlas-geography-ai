import tkinter as tk
from tkinter import scrolledtext
import re
import os
from google import genai
from google.genai import types
import tkintermapview 
import requests 

class AtlasChatApp:
    def __init__(self, root): #This starts the app and sets up the window, the API client, and the chat thread with instructions
        self.root = root
        self.root.title("Atlas: The Best Geography Guide & Live Mapping Bot")
        self.root.geometry("1000x600")
        self.root.configure(bg="#7bd8f0") 
        
        env_keys = {}
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    cleaned_line = line.strip()
                    if "=" in cleaned_line and not cleaned_line.startswith("#"):
                        k, v = cleaned_line.split("=", 1)
                        env_keys[k.strip()] = v.strip()

        # Load keys securely from the file first, fallback to Windows Environment
        self.tomtom_api_key = env_keys.get("TOMTOM_API_KEY") or os.environ.get("TOMTOM_API_KEY")
        gemini_key = env_keys.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        
        if not gemini_key or not self.tomtom_api_key:
            print(" WARNING: API keys are missing! Check your .env file layout.")
        
        # Initialize AI Client
        self.client = genai.Client(api_key=gemini_key)
        self.atlas_chat = self.create_geography_chat()
    
        # Build layout frames
        self.create_layout()
        
        # Show introductory greeting
        self.display_message("Atlas", "Greetings, traveler! I am Atlas, your guide to the world's most interesting borders, countries, and natural phenomena. What corner of the globe shall we explore today?")

    def create_geography_chat(self):
        """Initializes the chat thread with instructions to attach map metadata tags."""
        system_instruction = (
            "You are 'Atlas', a very knowledgeable and precise geography scholar highly interested in"
            "the world's waterways, rivers, hidden seas, mountain ranges, enclaves, and weird borders.\n\n"
            "Rules:\n"
            "- You possess a flawless knowledge of global phenomena (tributaries, basins, sources, and mouths).\n"
            "- Sneak a fascinating, highly specific geographical fact about a river, lake, island, or border anomaly into every single answer, but they need to be quite short and very relevant.\n"
            "- Keep your tone witty, sharp, and engaging.\n\n"
            "CRITICAL MAP RULE:\n"
            "At the absolute end of your response, you MUST append a mapping token containing the singular main "
            "country or specific city/region name being discussed, wrapped strictly in brackets like this: [COUNTRY: Country Name]. "
            "For example: '...and that's how the enclave works! [COUNTRY: Netherlands]'. Always include this token!"
        )
        
        return self.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.8,
            )
        )

    def create_layout(self):
        """Creates a dual-pane interface: Left side for chat, Right side for map."""
        
        # === LEFT PANEL: CHAT INTERFACE ===
        left_frame = tk.Frame(self.root, bg="#7bd8f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 7), pady=15)
        
        # Top Banner for Chat Pane
        banner = tk.Label(left_frame, text="🌍 ATLAS CHAT", font=("Courier New", 13, "bold"), bg="#219ebc", fg="#ecf0f1", pady=8) 
        banner.pack(fill=tk.X)
        
        # Scrolled Text Box for Dialogue Histograph
        self.chat_display = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, font=("Arial", 11), bg="#f8f9fa", fg="#2c3e50", state=tk.DISABLED)
        self.chat_display.pack(pady=(10, 0), fill=tk.BOTH, expand=True)
        
        # Text Input Box and Send Layout Frame
        input_frame = tk.Frame(left_frame, bg="#7bd8f0")
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.entry_field = tk.Entry(input_frame, font=("Courier New", 12), bg="#ffffff", fg="#219ebc", borderwidth=2, relief=tk.FLAT)
        self.entry_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.entry_field.bind("<Return>", self.handle_send)
        self.entry_field.focus()
        
        send_button = tk.Button(input_frame, text="Send", font=("Courier New", 12, "bold"), bg="#e5be5a", fg="#ffffff", relief=tk.FLAT, width=10, command=self.handle_send)
        send_button.pack(side=tk.RIGHT, padx=(10, 0), ipady=6)
        
        # === RIGHT PANEL: INTERACTIVE LIVE MAP ===
        right_frame = tk.Frame(self.root, bg="#7bd8f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(7, 15), pady=15)
        
        # Map Frame Header Display Title
        map_banner = tk.Label(right_frame, text="LIVE GEO-TRACKING WINDOW", font=("Courier New", 13, "bold"), bg="#219ebc", fg="#ecf0f1", pady=8)
        map_banner.pack(fill=tk.X)
        
        # Initializing the OpenStreetMap Tile Renderer Widget
        self.map_widget = tkintermapview.TkinterMapView(right_frame, bg="#34495e")
        self.map_widget.pack(pady=(10, 0), fill=tk.BOTH, expand=True)
        
        # Set a default initial center coordinate point (Centered globally on Western Europe)
        self.map_widget.set_position(48.8566, 2.3522) 
        self.map_widget.set_zoom(4)

    def handle_send(self, event=None):
        """Captures input strings, queries Gemini, strips target tags, and snaps map viewpoints."""
        user_text = self.entry_field.get().strip()
        if not user_text:
            return
            
        self.entry_field.delete(0, tk.END)
        self.display_message("You", user_text)
        
        try:
            response = self.atlas_chat.send_message(user_text)
            raw_reply = response.text
            
            match = re.search(r'\[COUNTRY:\s*(.*?)\]', raw_reply, re.IGNORECASE)
            
            if match:
                extracted_location = match.group(1).strip()
                
                # Strip out the hidden metadata bracket completely so the user never sees it
                clean_reply = re.sub(r'\[COUNTRY:\s*.*?\]', '', raw_reply, flags=re.IGNORECASE).strip()
                self.display_message("Atlas", clean_reply)
                
                print(f"🗺️ Telemetry Hook Found! Attempting to pan map to: '{extracted_location}'")
                self.update_map_location(extracted_location)
            else:
                self.display_message("Atlas", raw_reply)
                print(" Telemetry missing: Atlas did not return a valid [COUNTRY: ...] tag this turn.")
                
        except Exception as e:
            self.display_message("System Error", f"Failed to sync telemetry layout: {e}")

    def update_map_location(self, location_name):
        """Queries the official TomTom API for coordinates and updates the map position."""
        try:
            query_string = location_name.strip()
            url = f"https://api.tomtom.com/search/2/geocode/{query_string}.json"
            
            params = {
                "key": self.tomtom_api_key,
                "limit": 1
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("results"):
                    position = data["results"][0]["position"]
                    lat = position["lat"]
                    lon = position["lon"]
                    
                    print(f" TomTom API Success! Found {query_string} at Coordinates: ({lat}, {lon})")
                    
                    self.map_widget.set_position(lat, lon)
                    self.map_widget.set_zoom(6) 
                    
                    # Clear old pins, drop a fresh pin right on the spot
                    self.map_widget.delete_all_marker()
                    self.map_widget.set_marker(lat, lon, text=query_string)
                else:
                    print(f" TomTom API couldn't find a matching location for: '{query_string}'")
            else:
                print(f" TomTom API returned an error status code: {response.status_code}")
                
        except Exception as e:
            print(f" Telemetry network error: {e}")

    def display_message(self, sender, text):
        """Locks/Unlocks state boxes to insert styled string dialogue text blocks."""
        self.chat_display.config(state=tk.NORMAL)
        if sender == "You":
            self.chat_display.insert(tk.END, f"\n You:\n{text}\n", "user_style")
        elif sender == "Atlas":
            self.chat_display.insert(tk.END, f"\n Atlas:\n{text}\n", "bot_style")
        else:
            self.chat_display.insert(tk.END, f"\n {sender}: {text}\n", "error_style")
            
        self.chat_display.tag_config("user_style", foreground="#2980b9", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("bot_style", foreground="#fb8500", font=("Arial", 11))
        self.chat_display.tag_config("error_style", foreground="#c0392b", font=("Arial", 11, "italic"))
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = AtlasChatApp(root)
    root.mainloop()
