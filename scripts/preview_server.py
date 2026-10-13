"""本地真机预览：静态服务 dist/ + 把 /api/* 反代到真实 Komari。

用途：让**未激活**的主题在真实数据下渲染（不需要把它切成线上主题），
用于出预览图与目视验收。默认端口 2602。
"""
import http.server
import pathlib
import socketserver
import urllib.error
import urllib.request

DIST = pathlib.Path('/root/komari-matsuri-glass/dist')
UPSTREAM = 'http://127.0.0.1:25774'
PORT = 2602


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIST), **kw)

    def log_message(self, fmt, *args):
        pass

    def _proxy(self):
        url = UPSTREAM + self.path
        body = None
        n = int(self.headers.get('Content-Length') or 0)
        if n:
            body = self.rfile.read(n)
        req = urllib.request.Request(url, data=body, method=self.command)
        for h in ('Content-Type', 'Authorization', 'Cookie', 'Accept'):
            if self.headers.get(h):
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
                self.send_response(r.status)
                for k, v in r.headers.items():
                    if k.lower() not in ('transfer-encoding', 'connection'):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path.startswith('/api/'):
            return self._proxy()
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        return self._proxy()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    print(f'预览服务器 http://127.0.0.1:{PORT}/  （静态 {DIST} + /api → {UPSTREAM}）', flush=True)
    Server(('127.0.0.1', PORT), Handler).serve_forever()
