"""Generate the SkySystem environment LUT (256x8 PNG).

Rows (top to bottom): zenith, horizon, halo, cloudLit, cloudShadow,
cloudRim, ambient, sun. X axis = time of day 0..24h.
Ported from the traditional.html 'cream daylight' reference preset.
Pure stdlib (zlib/struct) so it runs anywhere.
"""
import zlib, struct, os

ROWS = ['zenith', 'horizon', 'halo', 'cloudLit', 'cloudShadow', 'cloudRim', 'ambient', 'sun']
P = {
'zenith':[[0,'#070d24'],[0.21,'#0b1538'],[0.26,'#3b62b0'],[0.33,'#3a74cc'],[0.5,'#3d7ad8'],[0.62,'#3e72ca'],[0.7,'#4a64b4'],[0.76,'#3c3a82'],[0.81,'#141a45'],[1,'#070d24']],
'horizon':[[0,'#10193a'],[0.22,'#2c3461'],[0.25,'#ffb070'],[0.31,'#ffe2bc'],[0.5,'#ffe9c9'],[0.64,'#ffdfb4'],[0.71,'#ffba78'],[0.77,'#c2708e'],[0.82,'#2a2f60'],[1,'#10193a']],
'halo':[[0,'#22305c'],[0.23,'#ff8a48'],[0.27,'#ffc382'],[0.35,'#fff0d0'],[0.5,'#fff3d6'],[0.66,'#ffe2a8'],[0.72,'#ffa860'],[0.77,'#e06a78'],[0.81,'#33305e'],[1,'#22305c']],
'cloudLit':[[0,'#3c4a78'],[0.23,'#ffbe92'],[0.28,'#ffe2c0'],[0.35,'#fff3dc'],[0.5,'#fff5e0'],[0.64,'#ffefd2'],[0.71,'#ffd2a4'],[0.77,'#e8a2ae'],[0.81,'#5a6594'],[1,'#3c4a78']],
'cloudShadow':[[0,'#1a2244'],[0.23,'#7e62a0'],[0.3,'#a8acdc'],[0.5,'#aeb2e0'],[0.64,'#aaa6da'],[0.72,'#a082bc'],[0.78,'#4a4378'],[0.82,'#232c54'],[1,'#1a2244']],
'cloudRim':[[0,'#5c6ea8'],[0.24,'#ffce92'],[0.35,'#ffeac0'],[0.5,'#ffe9bc'],[0.66,'#ffdda2'],[0.73,'#ffb47e'],[0.79,'#6a74b4'],[1,'#5c6ea8']],
'ambient':[[0,'#0c1330'],[0.25,'#9a7078'],[0.35,'#bcc4e8'],[0.5,'#c9d4f0'],[0.66,'#c4b8d8'],[0.74,'#7a5c94'],[0.81,'#15204a'],[1,'#0c1330']],
'sun':[[0,'#aac4ff'],[0.24,'#ff9450'],[0.3,'#ffdfa6'],[0.5,'#fff4d8'],[0.66,'#ffe2a4'],[0.73,'#ff8e58'],[0.79,'#aac4ff'],[1,'#aac4ff']]
}

def h2rgb(h):
    return [int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)]

def sample(keys, t):
    for i in range(len(keys) - 1):
        t0, c0 = keys[i]
        t1, c1 = keys[i + 1]
        if t0 <= t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-5)
            u = u * u * (3 - 2 * u)
            a, b = h2rgb(c0), h2rgb(c1)
            return [a[k] + (b[k] - a[k]) * u for k in range(3)]
    return h2rgb(keys[-1][1])

W, H = 256, 8
raw = bytearray()
for r in range(H):
    raw.append(0)  # filter: none
    keys = P[ROWS[r]]
    for x in range(W):
        c = sample(keys, x / 255.0)
        raw += bytes([int(round(c[0])), int(round(c[1])), int(round(c[2])), 255])

def chunk(tag, d):
    return struct.pack(">I", len(d)) + tag + d + struct.pack(">I", zlib.crc32(tag + d) & 0xffffffff)

png = (b'\x89PNG\r\n\x1a\n'
       + chunk(b'IHDR', struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
       + chunk(b'IEND', b''))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "T_SkySystem_EnvLUT_256x8.png")
with open(out, "wb") as f:
    f.write(png)
print(out)
