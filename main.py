from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib.parse as urlparse
from urllib.parse import parse_qs
import translate as tr


curr_token = tr.get_auth(tr.KEY, tr.URL_AUTH)

hostName = "localhost"
serverPort = 8080

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):

        query = urlparse.urlparse(self.path)
        dict_params = parse_qs(query.query)
        if 'word' in dict_params:
            en_word = dict_params['word'][0]
            word_tr, infinitive = tr.minicard(en_word, tr.URL_TRANSLATE, curr_token)
            if word_tr is None:
                return
            use_example = tr.use_example(en_word, tr.tr_dict)
            if en_word != infinitive:
                result = f'{en_word} ({infinitive})\t{word_tr}{use_example}'
            else:
                result = f'{en_word}\t{word_tr}{use_example}'
            with open('words.txt', 'a', encoding='utf-8') as out:
                out.write(result + '\n')
            
            if en_word != infinitive:
                result = f'{word_tr}\t{en_word} ({infinitive}){use_example}'
            else:
                result = f'{word_tr}\t{en_word}{use_example}'
            with open('words_ru-en.txt', 'a', encoding='utf-8') as out:
                out.write(result + '\n')


        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Oke</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
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