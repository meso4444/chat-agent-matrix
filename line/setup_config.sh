#!/bin/bash
# Chat Agent Matrix (LINE) - Interactive Setup Wizard
# Helps generate .env environment file to protect sensitive information

ENV_FILE=".env"

# Load existing configuration as default values
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

echo "🤖 Chat Agent Matrix (LINE Edition) Setup Wizard"
echo "============================================="
echo "This script will help you configure sensitive credentials for LINE Bot and Cloudflare."
echo "Press Enter to keep existing settings shown in [brackets]."
echo ""

# Function: Read input with support for default values
get_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local is_secret="$4"

    local display_default="$default"
    if [ "$is_secret" == "true" ] && [ -n "$default" ]; then
        display_default="${default:0:5}******"
    fi

    if [ -n "$display_default" ]; then
        echo -e "📝 $prompt [Default: $display_default]"
    else
        echo -e "📝 $prompt"
    fi

    read -p "> " input

    if [ -z "$input" ]; then
        input="$default"
    fi

    # Export variable for later writing
    eval "$var_name=\"$input\""
}

# 1. LINE Channel Access Token
get_input "Enter LINE Channel Access Token" "$LINE_CHANNEL_ACCESS_TOKEN" "NEW_LINE_TOKEN" "true"
echo ""

# 2. LINE Channel Secret
get_input "Enter LINE Channel Secret" "$LINE_CHANNEL_SECRET" "NEW_LINE_SECRET" "true"
echo ""

# 3. Cloudflare Tunnel Name
# This is a name for the Tunnel, e.g., 'line-bot-tunnel'
get_input "Give your Cloudflare Tunnel a name (e.g., line-bot)" "${CLOUDFLARE_TUNNEL_NAME:-line-bot-tunnel}" "NEW_CF_NAME" "false"
echo ""

# 4. Cloudflare Custom Domain
# This is the complete subdomain, e.g., webhook.example.dpdns.org
echo "📝 Enter the full webhook URL (subdomain) you want to use"
echo "   Example: webhook.example.com"
echo "   (Note: You must have Cloudflare admin rights for example.com)"
get_input "URL" "$CLOUDFLARE_CUSTOM_DOMAIN" "NEW_CF_DOMAIN" "false"

# Write to .env
echo ""
echo "💾 Writing configuration to $ENV_FILE..."

cat > "$ENV_FILE" <<EOF
# LINE Bot Credentials
LINE_CHANNEL_ACCESS_TOKEN=$NEW_LINE_TOKEN
LINE_CHANNEL_SECRET=$NEW_LINE_SECRET

# Cloudflare Tunnel Configuration
CLOUDFLARE_TUNNEL_NAME=$NEW_CF_NAME
CLOUDFLARE_CUSTOM_DOMAIN=$NEW_CF_DOMAIN
EOF

echo "✅ Configuration complete!"
echo "👉 Next, please run ./setup_cloudflare_fixed_url.sh to establish connection"