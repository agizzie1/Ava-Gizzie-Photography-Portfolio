#!/usr/bin/env python3
# Adds new photos from the portfolio folders to index.html.
# For each photo not listed in tools/synced-photos.txt: makes a web-sized copy in images/,
# appends a <figure> to that folder's section, and updates the section's photo count.
# Usage: tools/sync-photos.py             add new photos
#        tools/sync-photos.py --baseline  mark every current photo as already added
import re, subprocess, sys, time
from datetime import datetime
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
STATE = SITE / "tools" / "synced-photos.txt"
PHOTO_TYPES = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff"}

# folder: (page, section id, which grid in the section (0 = first), image prefix, figure class)
FOLDERS = {
    "News":               ("index.html", "news",      0, "news",      "c4"),
    "Sports Photography": ("index.html", "sports",    0, "sports",    "c3"),
    "Portraits":          ("index.html", "portraits", 1, "portraits", "c4"),
    "Features:Opinions":  ("index.html", "features",  0, "features",  "c3"),
    "Photo Essay":        ("index.html", "essay",     0, "essay",     None),
    "Personal":           ("index.html", "personal",  0, "personal",  "c2"),
}
GRID = re.compile(r'<div class="(?:g6|g12|essay-frames)">')
MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]


def photos():
    for folder in FOLDERS:
        for p in sorted((ROOT / folder).iterdir()):
            if p.suffix.lower() in PHOTO_TYPES and not p.name.startswith("."):
                yield folder, p


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("'", "")).strip("-")


def title_for(stem):
    # "Swarthmore College - Men's Soccer 8 - 2026" -> "Swarthmore College Men's Soccer"
    if re.fullmatch(r"(DSC|IMG|A73)[_\d ]*\d.*", stem, re.I):
        return "Untitled"
    stem = re.sub(r"\.(png|jpe?g)$", "", stem, flags=re.I)
    stem = re.sub(r"\s*-\s*\d{4}$", "", stem)
    stem = re.sub(r"\s+\d+(?=\s*(-|$))", "", stem)
    return re.sub(r"\s*-\s*", " ", stem).strip()


def wait_until_copied(path):
    size = -1
    for _ in range(60):
        now = path.stat().st_size
        if now == size and now > 0:
            return
        size = now
        time.sleep(1)


def metadata(path):
    keys = ["kMDItemContentCreationDate", "kMDItemExposureTimeSeconds", "kMDItemFNumber",
            "kMDItemISOSpeed", "kMDItemFocalLength"]
    for _ in range(10):  # Spotlight can take a few seconds to index a new file
        out = subprocess.run(["mdls", *sum([["-name", k] for k in keys], []), str(path)],
                             capture_output=True, text=True).stdout
        meta = dict(re.findall(r"(\w+)\s+= (.+)", out))
        meta = {k: v.strip('"') for k, v in meta.items() if v != "(null)"}
        if "kMDItemExposureTimeSeconds" in meta or path.suffix.lower() == ".png":
            break
        time.sleep(1)
    return meta


def caption(title, meta, plain):
    parts = [] if plain else [f'<span class="dl">{title}.</span>']
    if "kMDItemContentCreationDate" in meta:
        d = datetime.strptime(meta["kMDItemContentCreationDate"], "%Y-%m-%d %H:%M:%S %z").astimezone()
        parts.append(f"{MONTHS[d.month - 1]} {d.day}, {d.year}.")
    elif plain:
        parts.append("Caption.")
    text = " ".join(parts)
    try:
        s = float(meta["kMDItemExposureTimeSeconds"])
        shutter = f"1/{round(1 / s)}" if s < 1 else f"{s:g}s"
        exif = [shutter, f"f/{float(meta['kMDItemFNumber']):g}",
                f"ISO {meta['kMDItemISOSpeed']}", f"{float(meta['kMDItemFocalLength']):g}mm"]
        text += f'<span class="exif">{" · ".join(exif)}</span>'
    except (KeyError, ValueError, ZeroDivisionError):
        pass
    return text


def make_web_copy(path, prefix):
    name = prefix + "--" + slugify(re.sub(r"(\.png)+$", "", path.stem, flags=re.I))
    out, n = SITE / "images" / f"{name}.jpg", 2
    while out.exists():
        out, n = SITE / "images" / f"{name}-{n}.jpg", n + 1
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "72", "-Z", "1800",
                    str(path), "--out", str(out)], check=True, capture_output=True)
    dims = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(out)],
                          capture_output=True, text=True).stdout
    w, h = re.findall(r"pixel(?:Width|Height): (\d+)", dims)
    return out.name, w, h


def figure(src, w, h, title, cap, cls):
    indent = " " * 10
    attr = f' class="{cls}"' if cls else ""
    return (f'\n{indent}<figure{attr}>\n'
            f'{indent}  <button class="frame" style="--ar:{w}/{h}">\n'
            f'{indent}    <img src="images/{src}" alt="{title}" width="{w}" height="{h}" loading="lazy">\n'
            f'{indent}  </button>\n'
            f'{indent}  <figcaption>{cap}</figcaption>\n'
            f'{indent}</figure>\n')


def insert(html, section, grid_index, block):
    start = html.index(f'<section id="{section}">')
    end = html.index("</section>", start)
    grid = list(GRID.finditer(html, start, end))[grid_index]
    depth, pos = 1, grid.end()
    for tag in re.finditer(r"<div\b|</div>", html[pos:]):
        depth += 1 if tag.group() == "<div" else -1
        if depth == 0:
            close = pos + tag.start()
            break
    before = html[:close].rstrip(" ")
    html = before + block + html[len(before):]
    # Update "<span>N photos</span>" in the section header
    end = html.index("</section>", start)
    count = html.count("<figure", start, end)
    head = re.compile(r"(<span>)\d+( photos</span>)")
    m = head.search(html, start, end)
    if m:
        html = html[:m.start()] + f"{m.group(1)}{count}{m.group(2)}" + html[m.end():]
    return html


def notify(message):
    subprocess.run(["osascript", "-e", f'display notification "{message}" with title "Portfolio updated"'],
                   capture_output=True)


def main():
    done = set(STATE.read_text().splitlines()) if STATE.exists() else set()
    found = [(folder, p) for folder, p in photos()]
    if "--baseline" in sys.argv:
        STATE.write_text("\n".join(sorted(f"{f}/{p.name}" for f, p in found)) + "\n")
        print(f"Marked {len(found)} photos as already added.")
        return

    added = {}
    for folder, path in found:
        key = f"{folder}/{path.name}"
        if key in done:
            continue
        page, section, grid_index, prefix, cls = FOLDERS[folder]
        wait_until_copied(path)
        src, w, h = make_web_copy(path, prefix)
        title = title_for(path.stem)
        block = figure(src, w, h, title, caption(title, metadata(path), cls is None), cls)
        html_path = SITE / page
        html_path.write_text(insert(html_path.read_text(), section, grid_index, block))
        with STATE.open("a") as f:
            f.write(key + "\n")
        added.setdefault(section, []).append(src)
        print(f"Added {key} -> images/{src} ({section})")

    if added:
        notify(", ".join(f"{len(v)} to {k}" for k, v in added.items()) + ". Edit captions and alt text.")
    else:
        print("No new photos.")


if __name__ == "__main__":
    main()
