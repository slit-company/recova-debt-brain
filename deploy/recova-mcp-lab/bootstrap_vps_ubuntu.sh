#!/usr/bin/env sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  printf '%s\n' "Run as root on the Ubuntu/Debian VPS." >&2
  exit 1
fi

. /etc/os-release
case "$ID" in
  ubuntu|debian)
    docker_repo_os="$ID"
    ;;
  *)
    printf '%s\n' "Unsupported OS: $ID. Use Ubuntu or Debian." >&2
    exit 1
    ;;
esac

apt-get update
apt-get install -y ca-certificates curl gnupg ufw

install -m 0755 -d /etc/apt/keyrings
rm -f /etc/apt/keyrings/docker.gpg
curl -fsSL "https://download.docker.com/linux/${docker_repo_os}/gpg" \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

printf '%s\n' \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${docker_repo_os} ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

mkdir -p /opt/recova-mcp-lab

printf '%s\n' "recova_mcp_vps_bootstrap=ready"
printf '%s\n' "Install path: /opt/recova-mcp-lab"
printf '%s\n' "Next: run scripts/recova_mcp/deploy_vps.sh user@host from the repo."
