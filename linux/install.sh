#!/usr/bin/env bash
set -euo pipefail

# ── paths ────────────────────────────────────────────────────────────────
APP_DIR="$HOME/.local/share/PTZController"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── colours ──────────────────────────────────────────────────────────────
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; N='\033[0m'
ok()   { echo -e "${G}  ✔  $*${N}"; }
info() { echo -e "${B}  ▸  $*${N}"; }
warn() { echo -e "${Y}  ⚠  $*${N}"; }
die()  { echo -e "${R}  ✘  $*${N}" >&2; exit 1; }

echo -e "${B}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║    PTZ Camera Controller — Installer     ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${N}"

# ── check Python 3 ───────────────────────────────────────────────────────
info "Checking Python 3..."
command -v python3 &>/dev/null || die "python3 not found. Please install it first."
ok "$(python3 --version)"

# ── find a Python version with installable apt packages ──────────────────
# Ubuntu 26.04 can have a PPA/custom Python whose version is ahead of the
# Ubuntu repos, making python3.X-tk/venv apt packages uninstallable.
# We scan candidates (current version first, then 3.13/3.12 as fallbacks)
# and pick the first one apt can actually install.

SYSTEM_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
APP_PYTHON=""
APP_VER=""

info "Detecting best Python version for installation..."
sudo apt-get update -qq 2>/dev/null

for VER in "$SYSTEM_VER" "3.13" "3.12" "3.11"; do
    if sudo apt-get install -y --dry-run "python${VER}-tk" "python${VER}-venv" \
       >/dev/null 2>&1; then
        APP_VER="$VER"
        break
    fi
done

[[ -z "$APP_VER" ]] && die "Could not find a Python version (3.11–3.14) with installable apt packages."

# Install the Python runtime itself if it is not yet present
if ! command -v "python${APP_VER}" &>/dev/null; then
    info "Installing python${APP_VER}..."
    sudo apt-get install -y "python${APP_VER}"
fi

info "Installing system packages for Python ${APP_VER}..."
sudo apt-get install -y "python${APP_VER}-tk" "python${APP_VER}-venv"
ok "Using Python ${APP_VER} (system Python is ${SYSTEM_VER})"

APP_PYTHON="python${APP_VER}"

# ── create directories ───────────────────────────────────────────────────
mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR"

# ── copy app file ────────────────────────────────────────────────────────
info "Copying application files..."
cp "$SCRIPT_DIR/PTZController.py" "$APP_DIR/"
ok "Files installed to $APP_DIR"

# ── virtual environment ──────────────────────────────────────────────────
# Remove any previous (possibly broken) venv so we always start clean
[[ -d "$APP_DIR/venv" ]] && rm -rf "$APP_DIR/venv"
info "Creating Python virtual environment with ${APP_PYTHON}..."
# --system-site-packages lets the venv access the python3.X-tk installed above
"$APP_PYTHON" -m venv --system-site-packages "$APP_DIR/venv"

# Ensure pip is available (ubuntu may strip ensurepip; the venv package bundles it)
if ! "$APP_DIR/venv/bin/python3" -m pip --version &>/dev/null 2>&1; then
    info "Bootstrapping pip via ensurepip..."
    "$APP_DIR/venv/bin/python3" -m ensurepip --upgrade \
      || die "pip not available. Try: sudo apt install python${APP_VER}-pip"
fi
ok "Virtual environment ready"

info "Installing Python packages (this may take a minute)..."
"$APP_DIR/venv/bin/python3" -m pip install --quiet --upgrade pip
"$APP_DIR/venv/bin/python3" -m pip install "visca-over-ip" opencv-python
# Force pillow into the venv — the system python3-pil is compiled for a different
# Python version and causes an ImportError when accessed from this venv.
"$APP_DIR/venv/bin/python3" -m pip install --force-reinstall --quiet pillow
ok "Python packages installed"

# ── generate icon ────────────────────────────────────────────────────────
info "Generating application icon..."
"$APP_DIR/venv/bin/python3" - "$APP_DIR" <<'PYEOF'
from PIL import Image, ImageDraw
import sys, os

out = os.path.join(sys.argv[1], 'icon.png')
S   = 256
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d   = ImageDraw.Draw(img)

# Dark circular background
d.ellipse([4, 4, S-4, S-4], fill='#1a1a2e', outline='#e94560', width=5)

# Camera body
d.rounded_rectangle([44, 88, 212, 178], radius=12, fill='#e94560')

# Viewfinder notch (centred, sits on top of body)
d.rounded_rectangle([105, 70, 151, 92], radius=6, fill='#e94560')

# Flash (top-right corner of body)
d.rounded_rectangle([170, 94, 200, 110], radius=4, fill='#ffa500')

# Lens rings (centred in body)
cx, cy = 128, 133
d.ellipse([cx-40, cy-40, cx+40, cy+40], fill='#16213e', outline='#b8b8b8', width=3)
d.ellipse([cx-28, cy-28, cx+28, cy+28], fill='#0f3460', outline='#b8b8b8', width=2)
d.ellipse([cx-14, cy-14, cx+14, cy+14], fill='#1a1a2e')
d.ellipse([cx-5,  cy-5,  cx+5,  cy+5],  fill='#4488ff')

img.save(out)
print(f'    saved → {out}')
PYEOF
ok "Icon created"

# ── launcher script ──────────────────────────────────────────────────────
info "Creating launcher script..."
cat > "$BIN_DIR/ptzcontroller" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
exec "$APP_DIR/venv/bin/python3" "$APP_DIR/PTZController.py" "\$@"
EOF
chmod +x "$BIN_DIR/ptzcontroller"
ok "Launcher: $BIN_DIR/ptzcontroller"

# ── .desktop entry ───────────────────────────────────────────────────────
info "Installing desktop entry..."
cat > "$DESKTOP_DIR/ptzcontroller.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PTZ Camera Controller
GenericName=Camera Controller
Comment=Control PTZ cameras via VISCA over IP
Exec=$BIN_DIR/ptzcontroller
Icon=$APP_DIR/icon.png
Terminal=false
Categories=Video;AudioVideo;
Keywords=PTZ;camera;VISCA;pan;tilt;zoom;
StartupNotify=true
StartupWMClass=PTZController
EOF
chmod +x "$DESKTOP_DIR/ptzcontroller.desktop"

# Mark as trusted so GNOME doesn't show the "untrusted launcher" prompt
if command -v gio &>/dev/null; then
    gio set "$DESKTOP_DIR/ptzcontroller.desktop" metadata::trusted true 2>/dev/null || true
fi

# Rebuild the desktop database so the app appears in the menu immediately
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
ok "Desktop entry installed"

# ── PATH reminder ────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    warn "$BIN_DIR is not in your current PATH."
    echo "      Add the following line to your ~/.bashrc (or ~/.zshrc) and re-open your terminal:"
    echo -e "      ${Y}export PATH=\"\$HOME/.local/bin:\$PATH\"${N}"
    echo ""
fi

# ── done ─────────────────────────────────────────────────────────────────
echo -e "${G}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║       Installation complete!  ✔          ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${N}"
echo "  How to launch:"
echo -e "  ${B}1.${N} Open your application menu and search for  ${Y}PTZ Camera Controller${N}"
echo -e "  ${B}2.${N} Or run from a terminal:  ${Y}ptzcontroller${N}"
echo ""
