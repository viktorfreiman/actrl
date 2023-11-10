import http.server
import socketserver
import sys, signal

# basic rude http server
# signal will take next request and exit gracefully? bug?

def signal_handler(signal, frame):
    print("\nprogram exiting gracefully")
    sys.exit(0)

class Server(socketserver.TCPServer):
    # Avoid "address already used" error when frequently restarting the script
    allow_reuse_address = True


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # global done
        self.send_response(200, "OK")
        self.end_headers()
        self.wfile.write(f"It works! path {self.path}".encode("utf-8"))
        # done = True


signal.signal(signal.SIGINT, signal_handler)

with Server(("", 8888), Handler) as httpd:
    while True:
        httpd.handle_request()
