import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import json

initjson = """{
    "command": "selectunit",
    "targets":{
        "range": "screen", 
        "groupId" : [],  
        "type": ["e1"] 
    }
}
"""

class PacketSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Json Sender")

        # Set grid layout configuration
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=3)
        root.grid_columnconfigure(2, weight=1)
        root.grid_columnconfigure(3, weight=3)
        root.grid_columnconfigure(4, weight=1)

        # URL input
        self.url_label = tk.Label(root, text="URL:")
        self.url_label.grid(row=0, column=0, sticky=tk.E)
        self.url_entry = tk.Entry(root)
        self.url_entry.insert(tk.END, "http://localhost:8080")
        self.url_entry.grid(row=0, column=1, columnspan=3, padx = (0,95), sticky=tk.EW)

        # Request JSON
        self.request_label = tk.Label(root, text="Request JSON:")
        self.request_label.grid(row=1, column=0, sticky=tk.W)
        self.request_text = scrolledtext.ScrolledText(root, width=50, height=40)
        self.request_text.insert(tk.END, initjson)        
        self.request_text.grid(row=2, column=0, columnspan=2, padx = (20,20), sticky=tk.W+tk.E+tk.N+tk.S)

        # Response JSON
        self.response_label = tk.Label(root, text="Response:")
        self.response_label.grid(row=1, column=3, sticky=tk.W)
        self.response_text = scrolledtext.ScrolledText(root, width=50, height=40)
        self.response_text.grid(row=2, column=3, columnspan=2, padx = (20,20), sticky=tk.W+tk.E+tk.N+tk.S)

        # Send button
        self.send_button = tk.Button(root, text="Send Request", command=self.send_request)
        self.send_button.grid(row=3, column=1, columnspan=3, pady = 15, padx = (40,135),sticky=tk.EW)

    def send_request(self):
        url = self.url_entry.get()
        json_data = self.request_text.get("1.0", tk.END).strip()

        try:
            # Check if JSON is valid
            request_object = json.loads(json_data)

            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, data=json_data)

            if 'application/json' in response.headers.get('Content-Type', ''):
                response_data = response.json()
                self.response_text.insert(tk.END, "Response JSON:\n")
                self.response_text.insert(tk.END, json.dumps(response_data, indent=4))
            else:
                self.response_text.insert(tk.END, "Response Text:\n")
                self.response_text.insert(tk.END, response.text)

            self.response_text.see(tk.END)  # Scroll to the bottom of the response text area

        except ValueError as e:
            messagebox.showerror("Invalid JSON", "Invalid JSON format. Please check your input.")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Request Failed", f"Request failed: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PacketSenderApp(root)
    root.mainloop()
