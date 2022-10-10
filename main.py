from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib.parse as urlparse
from urllib.parse import parse_qs
import anki_importer as ank


anki_file = 'anki_en-en.txt'
translate_type = 'en-en' #'en-ru'

hostName = "localhost"
serverPort = 8080

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):

        query = urlparse.urlparse(self.path)
        dict_params = parse_qs(query.query)
        if 'word' in dict_params:
            en_word = dict_params['word'][0]
            if translate_type == 'en-en':
                html_out = ank.anki_write(en_word, anki_file)
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes('<html><link rel="icon" href="data:;base64,iVBORw0KGgo="><head><title>Oke</title></head>', 'utf-8'))
        self.wfile.write(bytes("<body>", "utf-8"))
        if 'word' in dict_params and translate_type == 'en-en':
            self.wfile.write(bytes(f'{en_word}<br><br>', 'utf-8'))
            self.wfile.write(bytes(html_out, 'utf-8'))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":

    #http://localhost:8080/?word=test

    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")