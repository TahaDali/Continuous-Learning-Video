"""Serve the offline course with HTTP byte ranges for video seeking.
Usage: python3 serve.py --port 8766
"""
import argparse, pathlib, re, http.server, functools, webbrowser
P=pathlib.Path(__file__).resolve().parent.parent/'player'
class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path=pathlib.Path(self.translate_path(self.path))
        if not path.is_file(): return super().send_head()
        f=path.open('rb');size=path.stat().st_size;start=0;end=size-1;partial=False
        requested=self.headers.get('Range','')
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested)
        if match:
            a,b=match.groups()
            if a:start=int(a);end=min(size-1,int(b)) if b else size-1
            elif b:start=max(0,size-int(b))
            if start>=size or start>end:
                f.close();self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
            partial=True
        self.send_response(206 if partial else 200);self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1));self.send_header('Cache-Control','no-cache')
        if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();self.remaining=end-start+1;f.seek(start);return f
    def copyfile(self,source,outputfile):
        remaining=getattr(self,'remaining',None)
        try:
            while remaining is None or remaining>0:
                data=source.read(min(1024*128,remaining) if remaining is not None else 1024*128)
                if not data:break
                outputfile.write(data)
                if remaining is not None:remaining-=len(data)
        except (BrokenPipeError,ConnectionResetError):pass
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8766);ap.add_argument('--open',action='store_true');ap.add_argument('--directory',type=pathlib.Path,default=P);a=ap.parse_args()
    directory=a.directory.expanduser().resolve()
    if not (directory/'index.html').is_file():ap.error('Player directory must contain index.html')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),functools.partial(RangeHandler,directory=str(directory)))
    url=f'http://127.0.0.1:{server.server_address[1]}'
    print(f'Course player: {url}',flush=True)
    if a.open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
