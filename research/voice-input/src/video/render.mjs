// Снимает video.html покадрово и собирает MP4 для постов.
//
//   node render.mjs en            → voice-input-en.mp4 рядом с этим файлом
//   node render.mjs ru 12.5       → один кадр на 12,5 секунде в frame-ru.png (проверка)
//
// Нужны playwright-core (npm i playwright-core, браузер не качает — берёт
// установленный Chrome) и ffmpeg. Кадры идут в ffmpeg по трубе, на диск не пишутся.
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const lang = process.argv[2] || 'en';
const still = process.argv[3];
const FPS = 30;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const browser = await chromium.launch({ executablePath: CHROME });
const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(HERE, 'video.html')).href + '?lang=' + lang);
await page.evaluate(() => document.fonts.ready);
const DUR = await page.evaluate(() => window.DUR);

if (still !== undefined) {
  await page.evaluate(t => window.render(t), Number(still));
  await page.screenshot({ path: path.join(HERE, `frame-${lang}.png`) });
  await browser.close();
  process.exit(0);
}

const out = path.join(HERE, `voice-input-${lang}.mp4`);
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
  { stdio: ['pipe', 'inherit', 'inherit'] });

const N = Math.round(DUR * FPS);
for (let i = 0; i < N; i++) {
  await page.evaluate(t => window.render(t), i / FPS);
  const png = await page.screenshot({ type: 'png' });
  if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 150 === 0) process.stdout.write(`${lang} ${i}/${N}\n`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log(out);
