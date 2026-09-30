#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ролик для соцсетей: video.html рисует кадр за кадром в headless Chromium,
ffmpeg собирает MP4 (H.264, yuv420p, faststart — такой примут все площадки).

    python3 research/population/src/video/render.py                  # en, 1080×1350
    python3 research/population/src/video/render.py ru 1920x1080 out.mp4
    python3 research/population/src/video/render.py en 1080x1350 --stills 2,9,17,29

Нужны: python-пакет playwright с его Chromium и ffmpeg. Шрифты страница берёт
из Google Fonts, так что нужна сеть. Данные — ../data.json, те же, что у страницы.
"""
import base64, functools, http.server, os, subprocess, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # research/population
from playwright.sync_api import sync_playwright


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    stills = next((a.split('=', 1)[1] if '=' in a else sys.argv[sys.argv.index(a) + 1]
                   for a in sys.argv[1:] if a.startswith('--stills')), None)
    if stills in args:
        args.remove(stills)
    lang = args[0] if args else 'en'
    w, h = map(int, (args[1] if len(args) > 1 else '1080x1350').split('x'))
    out = args[2] if len(args) > 2 else 'population-%s-%dx%d.mp4' % (lang, w, h)
    fps = 30
    srv = serve()
    url = 'http://127.0.0.1:%d/src/video/video.html?lang=%s&w=%d&h=%d&fps=%d' % (srv.server_port, lang, w, h, fps)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': w, 'height': h})
        pg.goto(url)
        pg.wait_for_function('window.READY === true', timeout=60000)
        if stills:
            for t in stills.split(','):
                png = base64.b64decode(pg.evaluate('t => at(t)', float(t)).split(',', 1)[1])
                name = '%s-%s-%dx%d-t%s.png' % (os.path.splitext(out)[0], lang, w, h, t)
                open(name, 'wb').write(png)
                print(name)
            br.close()
            return
        n = pg.evaluate('FRAMES')
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'png', '-i', '-',
                               '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p',
                               '-profile:v', 'high', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        for i in range(n):
            ff.stdin.write(base64.b64decode(pg.evaluate('i => frame(i)', i).split(',', 1)[1]))
            if i % 150 == 0:
                print('кадр %d из %d' % (i, n), flush=True)
        ff.stdin.close()
        ff.wait()
        br.close()
    print(out, os.path.getsize(out), 'байт')


if __name__ == '__main__':
    main()
