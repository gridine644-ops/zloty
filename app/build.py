"""Builds the Złoty Plan Android app from the site's index.html.

  python3 build.py www      -> www/ with every library and font stored inside (works offline)
  python3 build.py android  -> icon, splash, colours and version for the generated android/ project
"""
import os, re, sys, shutil, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME_UA = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36'
BG = (6, 16, 20)


def get(url, ua=CHROME_UA):
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def build_www():
    src = open(os.path.join(HERE, '..', 'index.html'), encoding='utf-8').read()
    # the app has no service worker, web manifest or site icons
    src = re.sub(r"<script>if \('serviceWorker'.*?</script>", '', src, flags=re.S)
    src = re.sub(r'<link rel="(?:manifest|icon|apple-touch-icon|preconnect)"[^>]*>\n?', '', src)
    www = os.path.join(HERE, 'www')
    shutil.rmtree(www, ignore_errors=True)
    os.makedirs(os.path.join(www, 'lib'))
    os.makedirs(os.path.join(www, 'fonts'))
    libs = {
        'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js': 'lib/three.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js': 'lib/xlsx.full.min.js',
    }
    for url, local in libs.items():
        if url not in src:
            sys.exit('library URL not found in index.html: ' + url)
        open(os.path.join(www, local), 'wb').write(get(url))
        src = src.replace(url, local)
    m = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/css2[^"]+)">', src)
    if not m:
        sys.exit('Google Fonts link not found in index.html')
    css = get(m.group(1).replace('&amp;', '&')).decode('utf-8')
    urls = sorted(set(re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css)))
    for i, u in enumerate(urls):
        name = 'f%02d.woff2' % i
        open(os.path.join(www, 'fonts', name), 'wb').write(get(u))
        css = css.replace(u, name)
    open(os.path.join(www, 'fonts', 'fonts.css'), 'w', encoding='utf-8').write(css)
    src = src.replace(m.group(0), '<link rel="stylesheet" href="fonts/fonts.css">')
    open(os.path.join(www, 'index.html'), 'w', encoding='utf-8').write(src)
    print('www ready: %d font files, %d libraries' % (len(urls), len(libs)))


def patch_android():
    from PIL import Image
    res = os.path.join(HERE, 'android', 'app', 'src', 'main', 'res')
    icon = Image.open(os.path.join(HERE, 'icon-512.png')).convert('RGBA')
    fg = Image.open(os.path.join(HERE, 'icon-foreground.png')).convert('RGBA')
    legacy = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
    for dens, size in legacy.items():
        folder = os.path.join(res, 'mipmap-' + dens)
        os.makedirs(folder, exist_ok=True)
        small = icon.resize((size, size), Image.LANCZOS)
        small.save(os.path.join(folder, 'ic_launcher.png'))
        small.save(os.path.join(folder, 'ic_launcher_round.png'))
        fg.resize((size * 108 // 48, size * 108 // 48), Image.LANCZOS).save(os.path.join(folder, 'ic_launcher_foreground.png'))
    bgxml = os.path.join(res, 'values', 'ic_launcher_background.xml')
    if os.path.exists(bgxml):
        txt = open(bgxml, encoding='utf-8').read()
        open(bgxml, 'w', encoding='utf-8').write(re.sub(r'#[0-9A-Fa-f]{6,8}', '#061014', txt))
    splashes = 0
    for root, _, files in os.walk(res):
        for fn in files:
            if fn == 'splash.png':
                path = os.path.join(root, fn)
                w, h = Image.open(path).size
                sp = Image.new('RGB', (w, h), BG)
                s = max(48, int(min(w, h) * 0.28))
                c = icon.resize((s, s), Image.LANCZOS)
                sp.paste(c, ((w - s) // 2, (h - s) // 2), c)
                sp.save(path)
                splashes += 1
    colors = os.path.join(res, 'values', 'colors.xml')
    if os.path.exists(colors):
        txt = open(colors, encoding='utf-8').read()
        txt = re.sub(r'(name="colorPrimary(?:Dark)?">)#[0-9A-Fa-f]{6,8}', r'\g<1>#091012', txt)
        txt = re.sub(r'(name="colorAccent">)#[0-9A-Fa-f]{6,8}', r'\g<1>#E6BC5E', txt)
        open(colors, 'w', encoding='utf-8').write(txt)
    gradle = os.path.join(HERE, 'android', 'app', 'build.gradle')
    run = os.environ.get('GITHUB_RUN_NUMBER', '1')
    txt = open(gradle, encoding='utf-8').read()
    txt = re.sub(r'versionCode \d+', 'versionCode ' + run, txt)
    txt = re.sub(r'versionName "[^"]*"', 'versionName "1.%s"' % run, txt)
    open(gradle, 'w', encoding='utf-8').write(txt)
    print('android patched: icons, %d splash images, colours, version 1.%s' % (splashes, run))


if __name__ == '__main__':
    {'www': build_www, 'android': patch_android}[sys.argv[1]]()
