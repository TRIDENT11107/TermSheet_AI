import os
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

# Define the port for our server
PORT = 8000

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def log_message(self, format, *args):
        # Suppress log messages
        return

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Server running at http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(1)
    
    # Open the browser
    webbrowser.open(f"http://localhost:{PORT}/standalone.html")
    
    print("\nTermSheet AI is now running!")
    print(f"Access the application at: http://localhost:{PORT}/standalone.html")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down TermSheet AI...")
        sys.exit(0)
