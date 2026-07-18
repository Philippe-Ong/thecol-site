# -*- coding: utf-8 -*-
"""Serveur de développement pour le site ThéCol.

Identique à `python -m http.server`, mais interdit la mise en cache :
chaque rechargement du navigateur récupère la dernière version des fichiers.
Usage : python serve.py  →  http://localhost:8123
"""
import http.server

PORT = 8123


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), NoCacheHandler) as httpd:
        print(f"Site ThéCol sur http://localhost:{PORT} (cache désactivé)")
        httpd.serve_forever()
