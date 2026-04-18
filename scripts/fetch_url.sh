#!/usr/bin/env bash
# Fetch a URL as Markdown via proxy cascade with paywall bypass.
# Self-contained: no external skill dependencies.
#
# Bypass strategies (learned from Bypass Paywalls Clean):
#   1. r.jina.ai / defuddle.md — proxy services
#   2. Site-specific bot UA + X-Forwarded-For (Googlebot/Bingbot)
#   3. Referer spoofing (Google/Facebook/Twitter)
#   4. Cookie clearing + social referer
#   5. AMP page redirect
#   6. JSON-LD article extraction from raw HTML
#   7. archive.today (with browser fallback for CAPTCHA)
#   8. agent-fetch
#
# Usage: fetch_url.sh <url> [proxy_url]
set -uo pipefail

URL="${1:?Usage: fetch_url.sh <url> [proxy_url]}"
PROXY="${2:-}"

# ── Paywall domain lists (from BPC source) ──────────────────────────

# Sites where Googlebot UA gets full content (SEO whitelist)
GOOGLEBOT_DOMAINS="wsj.com|barrons.com|ft.com|economist.com|theaustralian.com.au|thetimes.co.uk|telegraph.co.uk|zeit.de|handelsblatt.com|leparisien.fr|nzz.ch|usatoday.com|quora.com|lefigaro.fr|lemonde.fr|spiegel.de|sueddeutsche.de|frankfurter-allgemeine.de|wires.com|brisbanetimes.com.au|smh.com.au|theage.com.au"

# Sites where Bingbot UA works
BINGBOT_DOMAINS="haaretz.com|nzherald.co.nz|stratfor.com|themarker.com"

# Sites that allow social referral traffic
FACEBOOK_REF_DOMAINS="law.com|ftm.nl|law360.com|sloanreview.mit.edu"

# Sites with usable AMP versions
AMP_DOMAINS="wsj.com|bostonglobe.com|latimes.com|chicagotribune.com|seattletimes.com|theatlantic.com|wired.com|newyorker.com|washingtonpost.com|smh.com.au|theage.com.au|brisbanetimes.com.au"

# All known paywall domains (for generic bypass attempts)
PAYWALL_DOMAINS="nytimes.com|wsj.com|ft.com|economist.com|bloomberg.com|washingtonpost.com|newyorker.com|wired.com|theatlantic.com|medium.com|businessinsider.com|technologyreview.com|scmp.com|seattletimes.com|bostonglobe.com|latimes.com|chicagotribune.com|theglobeandmail.com|afr.com|thetimes.co.uk|telegraph.co.uk|spiegel.de|zeit.de|sueddeutsche.de|barrons.com|forbes.com|foreignaffairs.com|foreignpolicy.com|harvard.edu|newscientist.com|scientificamerican.com|theinformation.com|statista.com|handelsblatt.com|nzz.ch|leparisien.fr|lefigaro.fr|lemonde.fr|haaretz.com|nzherald.co.nz|theaustralian.com.au|smh.com.au|theage.com.au|quora.com|usatoday.com"

# ── Helper functions ─────────────────────────────────────────────────

_curl() {
  if [ -n "$PROXY" ]; then
    https_proxy="$PROXY" http_proxy="$PROXY" curl -sL "$@"
  else
    curl -sL "$@"
  fi
}

_has_content() {
  local content="$1"
  local line_count
  line_count=$(echo "$content" | wc -l | tr -d ' ')

  # Must have more than 8 lines of content
  [ "$line_count" -gt 8 ] || return 1

  # Must have substantial text (not just navigation)
  local char_count
  char_count=$(echo "$content" | wc -c | tr -d ' ')
  [ "$char_count" -gt 500 ] || return 1

  # Filter out common error / login-wall pages
  echo "$content" | grep -q "Don't miss what's happening" && return 1
  echo "$content" | grep -q "Access Denied" && return 1
  echo "$content" | grep -q "404 Not Found" && return 1
  echo "$content" | grep -q "403 Forbidden" && return 1

  return 0
}

_domain_matches() {
  # Check if URL matches any domain in a pipe-separated list
  local url="$1"
  local domains="$2"
  echo "$url" | grep -qE "$domains"
}

_is_paywall_content() {
  local content="$1"
  # Detect common paywall indicators in response body
  echo "$content" | grep -qiE '(subscribe to (continue|read|access|unlock)|paywall|premium[._]content|metered[._]paywall|article[._]limit|sign[._]in[._]to[._](continue|read)|create[._]a[._]free[._]account[._]to[._]unlock|membership[._]to[._]continue|subscribe now for full access|to continue reading|remaining free articles|has been removed|subscribe or|already a subscriber)' && return 0
  return 1
}

_is_captcha_page() {
  local content="$1"
  echo "$content" | grep -qiE '(security check|captcha|recaptcha|hcaptcha|please complete|cloudflare.*challenge|verify you are human)' && return 0
  return 1
}

# Extract article body from JSON-LD in HTML (BPC strategy #6)
_extract_jsonld_article() {
  local html="$1"
  # Many sites embed full articleBody in <script type="application/ld+json">
  echo "$html" | grep -o '"articleBody":"[^"]*"' | head -1 | sed 's/^"articleBody":"//;s/"$//' | sed 's/\\n/\n/g; s/\\"/"/g; s/\\\\/\\/g'
}

# Convert raw HTML to rough text (strip tags)
_html_to_text() {
  local html="$1"
  echo "$html" | sed \
    -e 's/<script[^>]*>.*<\/script>//gI' \
    -e 's/<style[^>]*>.*<\/style>//gI' \
    -e 's/<nav[^>]*>.*<\/nav>//gI' \
    -e 's/<footer[^>]*>.*<\/footer>//gI' \
    -e 's/<header[^>]*>.*<\/header>//gI' \
    -e 's/<[^>]*>//g' \
    -e 's/&amp;/\&/g' \
    -e 's/&lt;/</g' \
    -e 's/&gt;/>/g' \
    -e 's/&quot;/"/g' \
    -e 's/&#39;/'"'"'/g' \
    -e 's/&nbsp;/ /g' \
    -e 's/^[[:space:]]*$//' | sed '/^$/N;/^\n$/d'
}

_try_output() {
  local content="$1"
  if _has_content "$content"; then
    if ! _is_paywall_content "$content"; then
      echo "$content"
      exit 0
    fi
  fi
}

# ── Level 1: Proxy services ─────────────────────────────────────────

# 1a. r.jina.ai — wide coverage, preserves image links, often bypasses paywalls
OUT=$(_curl --max-time 20 "https://r.jina.ai/$URL" 2>/dev/null || true)
_try_output "$OUT"

# 1b. defuddle.md — cleaner output with YAML frontmatter
OUT=$(_curl --max-time 20 "https://defuddle.md/$URL" 2>/dev/null || true)
_try_output "$OUT"

# ── Level 2: Site-specific bot UA bypass (BPC core strategy) ─────────

# 2a. Googlebot — most effective strategy, ~50 sites in BPC
if _domain_matches "$URL" "$GOOGLEBOT_DOMAINS"; then
  OUT=$(_curl --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
    -H "X-Forwarded-For: 66.249.66.1" \
    -H "Referer: https://www.google.com/" \
    -H "Accept: text/html,application/xhtml+xml" \
    -b "" \
    "$URL" 2>/dev/null || true)

  # Try extracting JSON-LD articleBody first (many sites embed it)
  ARTICLE=$(_extract_jsonld_article "$OUT")
  if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
    # Got full article from JSON-LD
    TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
    echo "# ${TITLE:-Article}"
    echo ""
    echo "Source: $URL"
    echo ""
    echo "$ARTICLE"
    exit 0
  fi

  # Fallback: convert HTML to text
  TEXT=$(_html_to_text "$OUT")
  _try_output "$TEXT"
fi

# 2b. Bingbot — works for some sites where Googlebot doesn't
if _domain_matches "$URL" "$BINGBOT_DOMAINS"; then
  OUT=$(_curl --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" \
    -H "Referer: https://www.bing.com/" \
    -H "Accept: text/html,application/xhtml+xml" \
    -b "" \
    "$URL" 2>/dev/null || true)

  ARTICLE=$(_extract_jsonld_article "$OUT")
  if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
    TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
    echo "# ${TITLE:-Article}"
    echo ""
    echo "Source: $URL"
    echo ""
    echo "$ARTICLE"
    exit 0
  fi

  TEXT=$(_html_to_text "$OUT")
  _try_output "$TEXT"
fi

# ── Level 3: Generic paywall bypass (for all paywall domains) ────────

if _domain_matches "$URL" "$PAYWALL_DOMAINS"; then

  # 3a. Googlebot UA + X-Forwarded-For (BPC strategy: spoof search engine)
  OUT=$(_curl --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" \
    -H "X-Forwarded-For: 66.249.66.1" \
    -H "Referer: https://www.google.com/" \
    -H "Accept: text/html,application/xhtml+xml" \
    -b "" \
    "$URL" 2>/dev/null || true)

  # Try JSON-LD extraction
  ARTICLE=$(_extract_jsonld_article "$OUT")
  if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
    TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
    echo "# ${TITLE:-Article}"
    echo ""
    echo "Source: $URL"
    echo ""
    echo "$ARTICLE"
    exit 0
  fi

  TEXT=$(_html_to_text "$OUT")
  _try_output "$TEXT"

  # 3b. Bingbot UA
  OUT=$(_curl --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" \
    -H "Referer: https://www.bing.com/" \
    -H "Accept: text/html,application/xhtml+xml" \
    -b "" \
    "$URL" 2>/dev/null || true)

  ARTICLE=$(_extract_jsonld_article "$OUT")
  if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
    TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
    echo "# ${TITLE:-Article}"
    echo ""
    echo "Source: $URL"
    echo ""
    echo "$ARTICLE"
    exit 0
  fi

  TEXT=$(_html_to_text "$OUT")
  _try_output "$TEXT"

  # 3c. Facebook Referer (some sites allow social referral traffic)
  if _domain_matches "$URL" "$FACEBOOK_REF_DOMAINS"; then
    OUT=$(_curl --max-time 15 \
      -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36" \
      -H "Referer: https://www.facebook.com/" \
      -b "" \
      "$URL" 2>/dev/null || true)
    TEXT=$(_html_to_text "$OUT")
    _try_output "$TEXT"
  fi

  # 3d. Twitter Referer
  OUT=$(_curl --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36" \
    -H "Referer: https://t.co/" \
    -b "" \
    "$URL" 2>/dev/null || true)
  TEXT=$(_html_to_text "$OUT")
  _try_output "$TEXT"

  # 3e. AMP page redirect (BPC strategy: AMP paywalls are weaker)
  if _domain_matches "$URL" "$AMP_DOMAINS"; then
    # Try common AMP URL patterns
    for AMP_SUFFIX in "/amp" "?outputType=amp" ".amp.html" "?amp"; do
      AMP_URL="${URL}${AMP_SUFFIX}"
      # Skip if URL already ends with this suffix
      [[ "$URL" == *"$AMP_SUFFIX" ]] && continue

      OUT=$(_curl --max-time 15 "$AMP_URL" 2>/dev/null || true)
      ARTICLE=$(_extract_jsonld_article "$OUT")
      if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
        TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
        echo "# ${TITLE:-Article}"
        echo ""
        echo "Source: $URL"
        echo ""
        echo "$ARTICLE"
        exit 0
      fi

      TEXT=$(_html_to_text "$OUT")
      _try_output "$TEXT"
    done

    # Also try .html/amp pattern (e.g., WSJ)
    AMP_URL=$(echo "$URL" | sed 's|\.html$|\.amp.html|' | sed 's|/$|/amp|')
    if [ "$AMP_URL" != "$URL" ]; then
      OUT=$(_curl --max-time 15 "$AMP_URL" 2>/dev/null || true)
      ARTICLE=$(_extract_jsonld_article "$OUT")
      if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
        TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
        echo "# ${TITLE:-Article}"
        echo ""
        echo "Source: $URL"
        echo ""
        echo "$ARTICLE"
        exit 0
      fi

      TEXT=$(_html_to_text "$OUT")
      _try_output "$TEXT"
    fi
  fi

  # 3f. EU X-Forwarded-For (BPC strategy: some sites show content for EU IPs)
  OUT=$(_curl --max-time 15 \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36" \
    -H "X-Forwarded-For: 185.$((RANDOM % 256)).$((RANDOM % 256)).$((RANDOM % 256))" \
    -H "Referer: https://www.google.com/" \
    -b "" \
    "$URL" 2>/dev/null || true)

  ARTICLE=$(_extract_jsonld_article "$OUT")
  if [ -n "$ARTICLE" ] && [ ${#ARTICLE} -gt 200 ]; then
    TITLE=$(echo "$OUT" | grep -o '<title[^>]*>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1)
    echo "# ${TITLE:-Article}"
    echo ""
    echo "Source: $URL"
    echo ""
    echo "$ARTICLE"
    exit 0
  fi

  TEXT=$(_html_to_text "$OUT")
  _try_output "$TEXT"
fi

# ── Level 4: archive.today with CAPTCHA handling ────────────────────

ARCHIVE_URL="https://archive.today/newest/$URL"
ARCHIVE_OUT=$(_curl -sL "$ARCHIVE_URL" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  --max-time 20 2>/dev/null || true)

if _has_content "$ARCHIVE_OUT"; then
  if ! _is_captcha_page "$ARCHIVE_OUT"; then
    # Got actual archived content — extract text
    TEXT=$(_html_to_text "$ARCHIVE_OUT")
    if _has_content "$TEXT"; then
      echo "$TEXT"
      exit 0
    fi
  fi
fi

# archive.ph returned CAPTCHA
# Use special exit code 75 so the caller (Claude) can detect and handle it
echo "ARCHIVE_CAPTCHA:$ARCHIVE_URL" >&2
echo "⚠️  archive.ph needs human verification." >&2
echo "   The caller should open this URL in a browser for the user to solve the CAPTCHA," >&2
echo "   then retry this script." >&2
exit 75

# ── Level 5: Google cache ───────────────────────────────────────────

CACHE_URL="https://webcache.googleusercontent.com/search?q=cache:$URL"
OUT=$(_curl --max-time 15 "$CACHE_URL" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  2>/dev/null || true)

if _has_content "$OUT"; then
  TEXT=$(_html_to_text "$OUT")
  if _has_content "$TEXT"; then
    echo "$TEXT"
    exit 0
  fi
fi

# ── Level 6: agent-fetch (last resort local tool) ───────────────────

if command -v npx &>/dev/null; then
  OUT=$(npx --yes agent-fetch "$URL" --json 2>/dev/null || true)
  if [ -n "$OUT" ]; then
    echo "$OUT"
    exit 0
  fi
fi

echo "ERROR: All fetch methods failed for: $URL" >&2
echo "TIP: Try opening https://archive.today/newest/$URL in your browser manually" >&2
exit 1
