#!/bin/zsh
# Runs tools/sync-photos.py automatically whenever a photo folder changes.
# Usage: tools/install-auto-sync.sh             turn on
#        tools/install-auto-sync.sh --uninstall  turn off
set -e
label=com.avagizzie.portfolio-sync
plist=~/Library/LaunchAgents/$label.plist
site="${0:A:h:h}"
root="${site:h}"

launchctl bootout gui/$(id -u)/$label 2>/dev/null || true
if [[ "$1" == --uninstall ]]; then
  rm -f "$plist"
  echo "Auto-sync turned off."
  exit 0
fi

folders=""
for f in "News" "Sports Photography" "Portraits" "Features:Opinions" "Photo Essay" "Personal"; do
  folders+="    <string>$root/$f</string>"$'\n'
done

mkdir -p ~/Library/LaunchAgents
cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$site/tools/sync-photos.py</string>
  </array>
  <key>WatchPaths</key>
  <array>
$folders  </array>
  <key>ThrottleInterval</key><integer>5</integer>
  <key>StandardOutPath</key><string>$site/tools/sync-photos.log</string>
  <key>StandardErrorPath</key><string>$site/tools/sync-photos.log</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$plist"
echo "Auto-sync turned on. New photos in the portfolio folders will be added to index.html."
echo "Log: tools/sync-photos.log"
