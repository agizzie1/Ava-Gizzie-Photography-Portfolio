#!/bin/zsh
# Makes a web-sized copy of a photo in images/ and prints a <figure> block to paste into index.html.
# Usage: tools/resize-photo.sh "path/to/original.JPG" section--short-name
set -e
if [[ $# -ne 2 ]]; then
  echo 'Usage: tools/resize-photo.sh "path/to/original.JPG" section--short-name'
  exit 1
fi
src="$1"; name="$2"
dir="${0:A:h}/../images"
out="$dir/$name.jpg"

sips -s format jpeg -s formatOptions 72 -Z 1800 "$src" --out "$out" >/dev/null
w=$(sips -g pixelWidth "$out" | awk '/pixelWidth/{print $2}')
h=$(sips -g pixelHeight "$out" | awk '/pixelHeight/{print $2}')
echo "Saved images/$name.jpg (${w}x${h}, $(du -k "$out" | cut -f1) KB)"
echo
cat <<EOF
<figure class="c3">
  <button class="frame" style="--ar:$w/$h">
    <img src="images/$name.jpg" alt="Describe the photo" width="$w" height="$h" loading="lazy">
  </button>
  <figcaption><span class="dl">Title.</span> Caption.</figcaption>
</figure>
EOF
