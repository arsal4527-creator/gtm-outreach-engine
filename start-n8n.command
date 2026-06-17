#!/bin/zsh
# One-click launcher for the GTM outreach n8n instance.
# Double-click this file in Finder, or run it from Terminal.
export NODES_EXCLUDE="[]"
export N8N_RESTRICT_FILE_ACCESS_TO="/Users/app/Desktop/GTM_Jobs;/Users/app/gtm-job-scraper;/private/tmp/gtm_outreach;/tmp/gtm_outreach"
export NODE_OPTIONS="--dns-result-order=ipv4first"   # force IPv4 — this machine's IPv6 route to Google times out
echo "Starting n8n with Execute Command + file access enabled..."
echo "Leave this window open while using n8n. Open http://localhost:5678"
exec n8n
