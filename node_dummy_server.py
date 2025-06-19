
import http.server
import socketserver
import os
import signal
import sys
import datetime

PORT = 3000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Hello from Dummy Node.js Server (Python)! Time: {datetime.datetime.now().strftime('%H:%M:%S')}\n".encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress HTTP request logging
        pass

def start_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Dummy Node.js Server (Python) running on port {PORT}")
        httpd.serve_forever()

def signal_handler(sig, frame):
    print("Dummy Node.js Server received signal. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    start_server()
