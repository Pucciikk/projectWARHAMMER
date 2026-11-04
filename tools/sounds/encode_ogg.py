"""
Переводит tools/sounds/wav/*.wav в assets/warpbound/sounds/gun/*.ogg. Запускать внутри Blender: в нём есть кодек Vorbis (модуль aud).

    exec(open(r".../tools/sounds/encode_ogg.py", encoding="utf-8").read())
"""
import glob
import os

import aud

ROOT = r"C:/Users/Name/projectWARHAMMER"
for src, dst in (("tools/sounds/wav", "gun"), ("tools/sounds/wav_dread", "dread")):
    DST = os.path.join(ROOT, "src/main/resources/assets/warpbound/sounds", dst)
    os.makedirs(DST, exist_ok=True)
    for wav in sorted(glob.glob(os.path.join(ROOT, src, "*.wav"))):
        name = os.path.basename(wav)[:-4]
        aud.Sound(wav).write(os.path.join(DST, name + ".ogg"), rate=44100, channels=aud.CHANNELS_MONO, format=aud.FORMAT_S16,
                             container=aud.CONTAINER_OGG, codec=aud.CODEC_VORBIS, bitrate=96000)
    print(dst, "ogg:", len(glob.glob(os.path.join(DST, "*.ogg"))))
