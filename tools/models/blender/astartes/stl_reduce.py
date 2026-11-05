"""
Сжатие тяжёлых STL вне Blender: читает двоичный STL, сливает вершины по сетке и пишет меньший STL.
Громовые воины весят по 490 МБ (около 10 млн граней), в Blender их напрямую грузить незачем.

    python tools/models/blender/astartes/stl_reduce.py <вход.stl> <выход.stl> [ячеек_на_высоту=700]
"""
import sys

import numpy as np


def read_stl(path):
    with open(path, "rb") as f:
        text = f.read(5) == b"solid" and b"facet" in f.read(300)
    if text:     # Громовые воины — текстовые STL
        vals = []
        with open(path, "rb") as f:
            for line in f:
                s = line.lstrip()
                if s.startswith(b"vertex"):
                    vals.append(s[6:])
        return np.array(b" ".join(vals).split(), dtype=np.float32).reshape(-1, 3, 3)
    with open(path, "rb") as f:
        f.seek(80)
        n = int(np.fromfile(f, dtype="<u4", count=1)[0])
        data = np.fromfile(f, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n)
    return data["v"]


def write_stl(path, tris):
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    out = np.zeros(len(tris), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    out["n"], out["v"] = n, tris
    with open(path, "wb") as f:
        f.write(b"warpbound reduced".ljust(80, b" "))
        np.array([len(tris)], dtype="<u4").tofile(f)
        out.tofile(f)


def reduce_stl(src, dst, cells=700):
    tri = read_stl(src)
    pts = tri.reshape(-1, 3)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    size = hi - lo
    cell = max(size) / cells
    keys = np.floor((pts - lo) / cell).astype(np.int64)
    k = keys[:, 0] * 4_000_000_000 + keys[:, 1] * 60_000 + keys[:, 2]
    uniq, inv = np.unique(k, return_inverse=True)
    sums = np.zeros((len(uniq), 3))
    np.add.at(sums, inv, pts.astype(np.float64))
    centers = (sums / np.bincount(inv)[:, None]).astype(np.float32)
    ids = inv.reshape(-1, 3)
    ok = (ids[:, 0] != ids[:, 1]) & (ids[:, 1] != ids[:, 2]) & (ids[:, 0] != ids[:, 2])
    ids = ids[ok]
    # одинаковые грани после слияния выбрасываем
    srt = np.sort(ids, axis=1)
    _, first = np.unique(srt, axis=0, return_index=True)
    ids = ids[np.sort(first)]
    write_stl(dst, centers[ids])
    print(f"{src}: граней {len(tri)} -> {len(ids)}, размер {size.round(1).tolist()}, низ {lo.round(1).tolist()}")


if __name__ == "__main__":
    reduce_stl(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 700)
