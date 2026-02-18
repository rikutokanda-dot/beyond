APP_SECRET="35e8ac43a9ba10f8a64960618d2f9581"
ACCESS_TOKEN="EAALda7TdQ3YBQhgWy8qVxaJMsatkQsmeyU0itOGOVPhWdA0ubRuwFvFro57oZAx2vgaczaZBxm51aK0UmjVoj4VK3wGRFgnMZBiyvB1AlJPTK7BejavvoX0lhl1b8LVJBJDt1Fs867BcE1LG5n1KcJRmKpW6hHlCwBKzI408H0ZCWZAkr3CbUHtSZC5WblgVg1wSjjxv0XMx3FbuNMizwJxm0DZCx5mWRjF"
APP_ID="806404619060086"
SYSTEM_USER_ID="61582305967240"
SCOPE="ads_management,ads_read" 

PROOF=$(echo -n "$ACCESS_TOKEN" | openssl dgst -sha256 -hmac "$APP_SECRET" | sed 's/^.* //')

curl -X POST \
  -F "business_app=$APP_ID" \
  -F "scope=$SCOPE" \
  -F "access_token=$ACCESS_TOKEN" \
  -F "appsecret_proof=$PROOF" \
  "https://graph.facebook.com/v24.0/$SYSTEM_USER_ID/access_tokens"
