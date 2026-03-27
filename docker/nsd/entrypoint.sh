#!/bin/sh
set -eu

RUNTIME_DIR="/runtime"
CERTS_DIR="${RUNTIME_DIR}/certs"
STATE_DIR="${RUNTIME_DIR}/state"
DYNAMIC_ZONE_DIR="${RUNTIME_DIR}/zones/dynamic"
NSD_CONF="/etc/nsd/nsd.conf"

mkdir -p "${CERTS_DIR}" "${STATE_DIR}" "${DYNAMIC_ZONE_DIR}"

if [ ! -f "${CERTS_DIR}/nsd_server.pem" ] || [ ! -f "${CERTS_DIR}/nsd_server.key" ] || [ ! -f "${CERTS_DIR}/nsd_control.pem" ] || [ ! -f "${CERTS_DIR}/nsd_control.key" ]; then
    echo "Generating NSD control TLS material in ${CERTS_DIR}"
    nsd-control-setup -d "${CERTS_DIR}"
fi

chmod 0644 \
    "${CERTS_DIR}/nsd_server.pem" \
    "${CERTS_DIR}/nsd_server.key" \
    "${CERTS_DIR}/nsd_control.pem" \
    "${CERTS_DIR}/nsd_control.key"

nsd-checkconf "${NSD_CONF}"

exec nsd -d -c "${NSD_CONF}"
