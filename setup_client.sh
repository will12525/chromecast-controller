#!/bin/bash
# Prepare a Raspberry Pi OS Lite machine as a local media client:
# Flask on port 5000, Chromium kiosk after tty1 autologin, HDMI kept on,
# Wi-Fi and Bluetooth disabled, USB disks automounted and served by http-server.
# Does not write server_url. Add that to app/config.json by hand when cloning.
# Calls setup.sh after USB mounts are recorded in config.cfg.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "RUN AS ROOT"
    exit 1
fi

if [[ -z "${SUDO_USER:-}" || "${SUDO_USER}" == "root" ]]; then
    echo "Run with sudo from the install user so autologin has an account"
    exit 1
fi

if [[ ! -r /proc/device-tree/model ]] || ! grep -a -q "Raspberry Pi" /proc/device-tree/model; then
    echo "This script only runs on a Raspberry Pi"
    exit 1
fi

WORKSPACE=$(cd "$(dirname "$0")" && pwd)
CONFIG_JSON="${WORKSPACE}/app/config.json"
SERVICES_DIR="${WORKSPACE}/system_services"
SYSTEMCTL_DIR=/etc/systemd/system
USER_UNIT_DIR=/etc/systemd/user
FSTAB=/etc/fstab
FSTAB_MARK="# chromecast-controller-client"
CONFIG_CFG="${WORKSPACE}/config.cfg"
FIRST_USB_MOUNT=""

if [[ ! -f "${CONFIG_JSON}" ]]; then
    echo "Missing: ${CONFIG_JSON}"
    exit 1
fi

install_user="${SUDO_USER}"
install_uid=$(id -u "${install_user}")
install_gid=$(id -g "${install_user}")
install_home=$(getent passwd "${install_user}" | cut -d: -f6)

boot_config() {
    if [[ -f /boot/firmware/config.txt ]]; then
        printf '%s' /boot/firmware/config.txt
    elif [[ -f /boot/config.txt ]]; then
        printf '%s' /boot/config.txt
    fi
}

boot_cmdline() {
    if [[ -f /boot/firmware/cmdline.txt ]]; then
        printf '%s' /boot/firmware/cmdline.txt
    elif [[ -f /boot/cmdline.txt ]]; then
        printf '%s' /boot/cmdline.txt
    fi
}

append_line_if_absent() {
    local file="$1"
    local line="$2"
    if [[ -z "${file}" || ! -f "${file}" ]]; then
        echo "Boot file missing; skipped: ${line}"
        return 0
    fi
    if grep -qxF "${line}" "${file}"; then
        return 0
    fi
    if [[ -s "${file}" ]] && [[ -n "$(tail -c1 "${file}")" ]]; then
        printf '\n' >> "${file}"
    fi
    printf '%s\n' "${line}" >> "${file}"
}

install_packages() {
    echo "Install system packages"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y chromium sway npm python3-venv sqlite3 ffmpeg exfatprogs ntfs-3g
    usermod -aG video,render,input "${install_user}"
}

install_flask_service() {
    echo "Installing chromecast_controller.service"
    sed -e "s,INSTALL_USER,${install_user},g" -e "s,INSTALL_DIR,${WORKSPACE},g" \
        "${SERVICES_DIR}/chromecast_controller.service" \
        > "${SYSTEMCTL_DIR}/chromecast_controller.service"
    systemctl enable chromecast_controller.service
}

install_kiosk() {
    echo "Installing tty1 autologin and the Chromium kiosk user service"
    mkdir -p "${SYSTEMCTL_DIR}/getty@tty1.service.d"
    cat > "${SYSTEMCTL_DIR}/getty@tty1.service.d/autologin.conf" <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${install_user} --noclear %I \$TERM
EOF

    mkdir -p "${USER_UNIT_DIR}" /etc/sway
    cp "${SERVICES_DIR}/sway_kiosk.conf" /etc/sway/kiosk.conf
    cp "${SERVICES_DIR}/chromium_kiosk.service" "${USER_UNIT_DIR}/chromium_kiosk.service"
    if [[ ! -d "${install_home}/.config" ]]; then
        mkdir -p "${install_home}/.config"
        chown "${install_user}:${install_user}" "${install_home}/.config"
    fi
    local wants="${install_home}/.config/systemd/user/default.target.wants"
    mkdir -p "${wants}"
    ln -sfn "${USER_UNIT_DIR}/chromium_kiosk.service" "${wants}/chromium_kiosk.service"
    chown -R "${install_user}:${install_user}" "${install_home}/.config/systemd"
}

keep_display_on() {
    echo "Disabling console blank, HDMI drop, and system sleep"
    local cmdline config
    cmdline=$(boot_cmdline)
    config=$(boot_config)
    if [[ -n "${cmdline}" ]]; then
        if ! grep -q 'consoleblank=0' "${cmdline}"; then
            sed -i 's/[[:space:]]*$//' "${cmdline}"
            sed -i 's/$/ consoleblank=0/' "${cmdline}"
        fi
        local connector token previous
        for connector in HDMI-A-1 HDMI-A-2; do
            token="video=${connector}:1920x1080M@60eD"
            previous="video=${connector}:1920x1080@60"
            if grep -q "${token}" "${cmdline}"; then
                continue
            fi
            if grep -q "${previous}" "${cmdline}"; then
                sed -i "s/${previous}/${token}/g" "${cmdline}"
                continue
            fi
            sed -i 's/[[:space:]]*$//' "${cmdline}"
            sed -i "s/\$/ ${token}/" "${cmdline}"
        done
    else
        echo "cmdline.txt not found; skipped consoleblank=0"
    fi
    if [[ -n "${config}" ]]; then
        if grep -q '^hdmi_force_hotplug=' "${config}"; then
            sed -i 's/^hdmi_force_hotplug=.*/hdmi_force_hotplug=1/' "${config}"
        else
            printf '\n%s\n' 'hdmi_force_hotplug=1' >> "${config}"
        fi
    else
        echo "config.txt not found; skipped hdmi_force_hotplug"
    fi

    local logind=/etc/systemd/logind.conf
    if [[ ! -f "${logind}" ]]; then
        printf '%s\n' '[Login]' 'IdleAction=ignore' > "${logind}"
    elif grep -q '^IdleAction=' "${logind}"; then
        sed -i 's/^IdleAction=.*/IdleAction=ignore/' "${logind}"
    elif grep -q '^\[Login\]' "${logind}"; then
        sed -i '/^\[Login\]/a IdleAction=ignore' "${logind}"
    else
        printf '\n%s\n%s\n' '[Login]' 'IdleAction=ignore' >> "${logind}"
    fi

    systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
}

disable_radios() {
    echo "Disabling Wi-Fi and Bluetooth"
    local config
    config=$(boot_config)
    append_line_if_absent "${config}" "dtoverlay=disable-wifi"
    append_line_if_absent "${config}" "dtoverlay=disable-bt"

    local unit
    for unit in bluetooth hciuart wpa_supplicant; do
        if systemctl list-unit-files "${unit}.service" --no-legend --no-pager 2>/dev/null | grep -q .; then
            systemctl disable --now "${unit}.service" || true
        fi
    done
}

sanitize_name() {
    local raw="$1"
    raw=$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/_/g; s/__*/_/g; s/^_//; s/_$//')
    if [[ -z "${raw}" ]]; then
        raw="disk"
    fi
    printf '%s' "${raw}"
}

root_block() {
    local src
    src=$(findmnt -n -o SOURCE / 2>/dev/null || true)
    if [[ -z "${src}" ]]; then
        return 0
    fi
    readlink -f "${src}" 2>/dev/null || printf '%s' "${src}"
}

fstab_mount_for_uuid() {
    local uuid="$1"
    awk -v uuid="${uuid}" '
        $0 ~ /^[[:space:]]*#/ { next }
        $1 == "UUID=" uuid { print $2; exit }
    ' "${FSTAB}"
}

uuid_in_fstab() {
    local uuid="$1"
    [[ -n "$(fstab_mount_for_uuid "${uuid}")" ]]
}

append_fstab() {
    local uuid="$1"
    local mount_point="$2"
    local fstype="$3"
    local options="nofail,x-systemd.device-timeout=10,x-systemd.automount"
    if [[ "${fstype}" == "vfat" || "${fstype}" == "exfat" || "${fstype}" == "ntfs" ]]; then
        options="nofail,uid=${install_uid},gid=${install_gid},x-systemd.device-timeout=10,x-systemd.automount"
    fi
    if [[ -s "${FSTAB}" ]] && [[ -n "$(tail -c1 "${FSTAB}")" ]]; then
        printf '\n' >> "${FSTAB}"
    fi
    printf '%s UUID=%s\n' "${FSTAB_MARK}" "${uuid}" >> "${FSTAB}"
    printf 'UUID=%s %s %s %s 0 0\n' "${uuid}" "${mount_point}" "${fstype}" "${options}" >> "${FSTAB}"
}

list_usb_filesystems() {
    python3 - <<'PY'
import json, subprocess, sys

raw = subprocess.check_output(
    ["lsblk", "-J", "-o", "NAME,TYPE,TRAN,FSTYPE,UUID,LABEL,PKNAME"],
    text=True,
)
tree = json.loads(raw).get("blockdevices") or []
def walk(nodes, parent_tran):
    for node in nodes:
        name = node.get("name") or ""
        tran = node.get("tran") or parent_tran or ""
        fstype = node.get("fstype") or ""
        uuid = node.get("uuid") or ""
        if tran == "usb" and fstype and uuid and node.get("type") in ("part", "disk"):
            label = (node.get("label") or "").replace("\t", " ").replace("\n", " ")
            sys.stdout.write("\t".join([uuid, fstype, label, name]) + "\n")
        walk(node.get("children") or [], tran)

walk(tree, "")
PY
}

setup_usb_disks() {
    echo "Looking for USB disks"
    local root_dev
    root_dev=$(root_block)
    local records=""
    local seen=" "
    local uuid fstype label name mount_point slug
    while IFS=$'\t' read -r uuid fstype label name; do
        [[ -z "${uuid}" ]] && continue
        if [[ " ${seen} " == *" ${uuid} "* ]]; then
            continue
        fi
        seen="${seen} ${uuid}"
        if [[ -n "${root_dev}" && "${root_dev}" == "/dev/${name}" ]]; then
            echo "Skipping root filesystem /dev/${name}"
            continue
        fi
        case "${fstype}" in
            ext4|vfat|exfat|ntfs) ;;
            *)
                echo "Skipping unsupported filesystem ${fstype} on /dev/${name}"
                continue
                ;;
        esac
        if uuid_in_fstab "${uuid}"; then
            mount_point=$(fstab_mount_for_uuid "${uuid}")
            echo "USB ${uuid} already in fstab at ${mount_point}"
        else
            slug=$(sanitize_name "${label:-${uuid}}")
            mount_point="/media/usb/${slug}"
            if [[ -n "$(fstab_mount_for_uuid_path "${mount_point}")" ]]; then
                mount_point="/media/usb/${slug}_$(printf '%s' "${uuid}" | tr -cd '[:alnum:]' | cut -c1-8)"
            fi
            mkdir -p "${mount_point}"
            append_fstab "${uuid}" "${mount_point}" "${fstype}"
            echo "Automount ${uuid} at ${mount_point}"
        fi
        mkdir -p "${mount_point}"
        if [[ -z "${FIRST_USB_MOUNT}" ]]; then
            FIRST_USB_MOUNT="${mount_point}"
        fi
        records="${records}${mount_point}"$'\n'
    done < <(list_usb_filesystems)

    if [[ -z "${records}" ]]; then
        echo "No USB filesystems found. Kiosk setup will continue."
    fi

    local mounts_file pairs
    mounts_file=$(mktemp)
    pairs=$(mktemp)
    printf '%s' "${records}" > "${mounts_file}"
    python3 - "${CONFIG_JSON}" "${pairs}" "${mounts_file}" <<'PY'
import json, sys

config_path, out_path, mounts_path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(mounts_path) as handle:
    mounts = [line for line in handle.read().splitlines() if line]
with open(config_path) as handle:
    cfg = json.load(handle)

def norm(path):
    if not isinstance(path, str) or not path.strip():
        return ""
    stripped = path.rstrip("/")
    return stripped or "/"

folders = cfg.get("media_folders")
if not isinstance(folders, list):
    folders = []

def port_of(url):
    if not isinstance(url, str) or ":" not in url:
        return None
    tail = url.rsplit(":", 1)[-1]
    digits = ""
    for char in tail:
        if char.isdigit():
            digits += char
        else:
            break
    return int(digits) if digits else None

used = set()
by_src = {}
for item in folders:
    if not isinstance(item, dict):
        continue
    src = norm(item.get("content_src", ""))
    port = port_of(item.get("content_url", ""))
    if port is not None:
        used.add(port)
    if src:
        by_src[src] = port

def take_port():
    port = 8000
    while port in used:
        port += 1
    used.add(port)
    return port

planned = []
for mount in mounts:
    key = norm(mount)
    if key in by_src and by_src[key] is not None:
        planned.append((mount, by_src[key]))
        continue
    port = take_port()
    if key not in by_src:
        folders.append({
            "content_src": mount,
            "content_url": f"http://127.0.0.1:{port}/",
        })
        by_src[key] = port
    planned.append((mount, port))

cfg["mode"] = "CLIENT"
cfg["media_folders"] = folders
with open(config_path, "w") as handle:
    json.dump(cfg, handle, indent=4)
    handle.write("\n")
with open(out_path, "w") as handle:
    for mount, port in planned:
        handle.write(f"{mount}\t{port}\n")
PY

    systemctl daemon-reload
    local mount port unit
    while IFS=$'\t' read -r mount port; do
        [[ -z "${mount}" ]] && continue
        unit="${SYSTEMCTL_DIR}/media_drive_${port}.service"
        sed -e "s,INSTALL_USER,${install_user},g" \
            -e "s,INSTALL_DIR,${mount},g" \
            -e "s,http-server -p 8000,http-server -p ${port}," \
            -e "/^After=network.target/a RequiresMountsFor=${mount}" \
            "${SERVICES_DIR}/media_drive_as_webpage.service" \
            > "${unit}"
        systemctl enable "media_drive_${port}.service"
        echo "http-server for ${mount} on port ${port}"
    done < "${pairs}"
    rm -f "${pairs}" "${mounts_file}"
}

# Mount path already claimed in fstab (any UUID).
fstab_mount_for_uuid_path() {
    local mount_point="$1"
    awk -v mount="${mount_point}" '
        $0 ~ /^[[:space:]]*#/ { next }
        $2 == mount { print $1; exit }
    ' "${FSTAB}"
}

write_media_dir() {
    local mount="$1"
    local current=""
    if [[ ! -f "${CONFIG_CFG}" ]]; then
        if [[ -z "${mount}" ]]; then
            printf '%s\n' 'MEDIA_DIR=' 'EDITOR_DIR=' > "${CONFIG_CFG}"
            return 0
        fi
        printf 'MEDIA_DIR="%s"\nEDITOR_DIR=\n' "${mount}" > "${CONFIG_CFG}"
        return 0
    fi
    # shellcheck source=./config.cfg
    source "${CONFIG_CFG}"
    current="${MEDIA_DIR:-}"
    if [[ -n "${current}" || -z "${mount}" ]]; then
        return 0
    fi
    python3 - "${CONFIG_CFG}" "${mount}" <<'PY'
import sys
path, mount = sys.argv[1], sys.argv[2]
quoted = '"' + mount.replace("\\", "\\\\").replace('"', '\\"') + '"'
lines = open(path).read().splitlines()
found = False
out = []
for line in lines:
    if line.startswith("MEDIA_DIR=") and not found:
        out.append("MEDIA_DIR=" + quoted)
        found = True
    else:
        out.append(line)
if not found:
    out.append("MEDIA_DIR=" + quoted)
with open(path, "w") as handle:
    handle.write("\n".join(out) + "\n")
PY
}

call_setup() {
    local media_dir=""
    if [[ -f "${CONFIG_CFG}" ]]; then
        # shellcheck source=./config.cfg
        source "${CONFIG_CFG}"
        media_dir="${MEDIA_DIR:-}"
    fi
    if [[ -n "${media_dir}" ]]; then
        (cd "${WORKSPACE}" && ./setup.sh)
        return
    fi
    echo "No MEDIA_DIR. Running setup.sh --deps-only."
    echo "Attach a USB disk and re-run setup_client.sh to record MEDIA_DIR and run the normal setup."
    (cd "${WORKSPACE}" && ./setup.sh --deps-only)
}

install_packages
setup_usb_disks
write_media_dir "${FIRST_USB_MOUNT}"
call_setup
install_flask_service
install_kiosk
keep_display_on
disable_radios

systemctl daemon-reload
systemctl enable chromecast_controller.service

echo "Client setup finished."
echo "Reboot so autologin, HDMI, and the Wi-Fi and Bluetooth overlays take effect."
echo "server_url was not changed. Edit ${CONFIG_JSON} when this client should clone from a server."
