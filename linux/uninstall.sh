#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$HOME/.local/share/PTZController"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; N='\033[0m'
ok()   { echo -e "${G}  ✔  $*${N}"; }
info() { echo -e "${B}  ▸  $*${N}"; }
warn() { echo -e "${Y}  ⚠  $*${N}"; }

echo -e "${B}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   PTZ Camera Controller — Uninstaller    ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${N}"

# Confirm before removing anything
read -r -p "  This will remove PTZ Camera Controller and all its files. Continue? [y/N] " reply
echo ""
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    warn "Cancelled — nothing was removed."
    exit 0
fi

# ── app files & venv ─────────────────────────────────────────────────────
if [[ -d "$APP_DIR" ]]; then
    info "Removing application files..."
    rm -rf "$APP_DIR"
    ok "Removed $APP_DIR"
else
    warn "$APP_DIR not found — skipping"
fi

# ── launcher script ──────────────────────────────────────────────────────
if [[ -f "$BIN_DIR/ptzcontroller" ]]; then
    info "Removing launcher..."
    rm -f "$BIN_DIR/ptzcontroller"
    ok "Removed $BIN_DIR/ptzcontroller"
else
    warn "$BIN_DIR/ptzcontroller not found — skipping"
fi

# ── desktop entry ────────────────────────────────────────────────────────
if [[ -f "$DESKTOP_DIR/ptzcontroller.desktop" ]]; then
    info "Removing desktop entry..."
    rm -f "$DESKTOP_DIR/ptzcontroller.desktop"
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    ok "Removed desktop entry"
else
    warn "$DESKTOP_DIR/ptzcontroller.desktop not found — skipping"
fi

# ── system packages (optional) ───────────────────────────────────────────
echo ""
read -r -p "  Remove installed system packages (python3.13, python3.13-tk, etc.)? [y/N] " reply2
echo ""
if [[ "$reply2" =~ ^[Yy]$ ]]; then
    info "Removing system packages..."
    sudo apt-get remove -y python3.13 python3.13-tk python3.13-venv \
         libpython3.13-minimal libpython3.13-stdlib python3.13-minimal \
         libtk8.6 python3-pip-whl python3-setuptools-whl 2>/dev/null || true
    sudo apt-get autoremove -y 2>/dev/null || true
    ok "System packages removed"
else
    warn "Skipped — system packages were left in place."
fi

echo -e "${G}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║        Uninstall complete.  ✔            ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${N}"
