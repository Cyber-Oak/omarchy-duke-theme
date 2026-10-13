#!/bin/bash
# Stage a few terminals on an empty workspace and screenshot them to
# preview.png. Apply the theme first (`omarchy theme set duke`) and make sure
# nothing draws over the wallpaper (e.g. a live-wallpaper shell plugin).
#
#   tools/capture-preview.sh [workspace]

set -euo pipefail

THEME_DIR=$(cd "$(dirname "$0")/.." && pwd)
WS=${1:-9}
FONT="JetBrainsMono Nerd Font:size=8"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cat >"$TMP/palette.sh" <<'EOF'
#!/bin/bash
printf '\n  \e[1;32mduke\e[0m  \e[2m— ANSI palette\e[0m\n\n'
names=(black red green yellow blue magenta cyan white)
for i in 0 1 2 3 4 5 6 7; do
  printf '  \e[3%dm%-8s\e[0m \e[9%dm%-7s\e[0m \e[4%dm    \e[0m\e[10%dm    \e[0m\n' "$i" "${names[$i]}" "$i" bright "$i" "$i"
done
printf '\n  \e[31merror\e[0m: build failed\n  \e[33mwarning\e[0m: unused variable\n  \e[34minfo\e[0m: 3 files changed\n'
printf '  \e[32m+ added line\e[0m\n  \e[31m- removed line\e[0m\n'
exec sleep 600
EOF
printf '#!/bin/bash\nfastfetch\nexec sleep 600\n' >"$TMP/fetch.sh"
# Code view: the theme's own generator, highlighted with the ANSI palette.
printf '#!/bin/bash\nbat --theme=ansi --style=numbers,grid --paging=never -r 60:110 "%s/tools/generate-backgrounds.py"\nexec sleep 600\n' "$THEME_DIR" >"$TMP/code.sh"
chmod +x "$TMP"/*.sh

launch() {
  hyprctl dispatch "hl.dsp.exec_cmd(\"foot --app-id=duke-preview -o 'font=$FONT' $1\")" >/dev/null
  sleep 1.2
}

hyprctl dispatch "hl.dsp.focus({ workspace = \"$WS\" })" >/dev/null
sleep 0.5
launch "$TMP/fetch.sh"
launch "$TMP/palette.sh"
launch "$TMP/code.sh"
sleep 2.5

grim "$THEME_DIR/preview.png"
echo "Wrote $THEME_DIR/preview.png"

# Close only the windows this script opened.
hyprctl clients -j |
  python3 -c 'import json,sys; [print(c["pid"]) for c in json.load(sys.stdin) if c["class"] == "duke-preview"]' |
  xargs -r kill
