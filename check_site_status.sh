#!/bin/bash

echo "🌐 Cherry AI Site Status Check"
echo "=============================="
echo ""

# Check which nameservers are active
echo "📡 Nameserver Status:"
CURRENT_NS=$(dig NS cherry-ai.me +short @8.8.8.8 | head -1)
if [[ "$CURRENT_NS" == *"ns-cloud-c"* ]]; then
    echo "✅ Using correct Vultr nameservers"
else
    echo "⏳ Nameservers still updating (currently: ${CURRENT_NS:-none})"
    echo "   Waiting for: ns-cloud-c1.googledomains.com"
fi

echo ""
# Check DNS propagation
echo "📍 DNS Resolution:"
CURRENT_IP=$(dig +short cherry-ai.me @8.8.8.8 | head -1)
EXPECTED_IP="34.160.252.197"

if [ "$CURRENT_IP" = "$EXPECTED_IP" ]; then
    echo "✅ DNS is pointing to your load balancer ($CURRENT_IP)"
else
    echo "⏳ DNS still showing old IPs. Current: ${CURRENT_IP:-none}"
    echo "   Expected: $EXPECTED_IP"
    # Check if correct nameservers have the right record
    GOOGLE_IP=$(dig +short cherry-ai.me @ns-cloud-c1.googledomains.com 2>/dev/null)
    if [ "$GOOGLE_IP" = "$EXPECTED_IP" ]; then
        echo "   ✓ Google DNS has correct record - waiting for nameserver switch"
    fi
fi

echo ""
echo "🔒 SSL Certificate Status:"
SSL_STATUS=$(gcloud compute ssl-certificates describe admin-ui-managed-cert-df09fd7 --global --format="value(managed.status)" 2>/dev/null)
DOMAIN_STATUS=$(gcloud compute ssl-certificates describe admin-ui-managed-cert-df09fd7 --global --format="value(managed.domainStatus[0])" 2>/dev/null)

if [ "$SSL_STATUS" = "ACTIVE" ]; then
    echo "✅ SSL certificate is ACTIVE"
else
    echo "⏳ SSL certificate is $SSL_STATUS"
    echo "   Domain status: ${DOMAIN_STATUS:-checking}"
    echo "   (Activates after DNS points to load balancer)"
fi

echo ""
echo "🌐 Site Status:"
if [ "$CURRENT_IP" = "$EXPECTED_IP" ] && [ "$SSL_STATUS" = "ACTIVE" ]; then
    echo "✅ Your site should be live at https://cherry-ai.me/"
    echo ""
    echo "Testing HTTPS connection..."
    HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}" https://cherry-ai.me/ 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Site is responding! Visit https://cherry-ai.me/"
    else
        echo "⚠️  HTTP Status: $HTTP_STATUS - Certificate may still be activating"
    fi
else
    echo "⏳ Waiting for:"
    [[ "$CURRENT_NS" != *"ns-cloud-c"* ]] && echo "   - Nameserver update at Squarespace"
    [ "$CURRENT_IP" != "$EXPECTED_IP" ] && echo "   - DNS propagation"
    [ "$SSL_STATUS" != "ACTIVE" ] && echo "   - SSL certificate activation"
    echo ""
    echo "⏰ This typically takes:"
    echo "   - Nameservers: 15 min to 2 hours"
    echo "   - DNS records: 5-30 minutes (after nameservers)"
    echo "   - SSL certificate: 10-20 minutes (after DNS)"
fi

echo ""
echo "Last checked: $(date)"
echo "Run again: ./check_site_status.sh"
