from flask import Flask, request, jsonify, Response
import requests
import random
import os

app = Flask(__name__)

PROXY_FILE = "proxiesyeah.txt"
TOKEN_FILE = "access_tokens.txt"

def load_proxies():
    """Load proxies from proxiesyeah.txt"""
    if not os.path.exists(PROXY_FILE):
        return []

    proxies = []
    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            proxies.append(line)
    return proxies

def format_proxy(proxy_str):
    """
    Convert different proxy formats into a proper URL
    that requests can use.
    """
    proxy_str = proxy_str.strip()

    # Already a full URL
    if proxy_str.startswith("http://") or proxy_str.startswith("https://"):
        return proxy_str

    # user:pass@host:port
    if "@" in proxy_str:
        return "http://" + proxy_str

    # host:port:user:pass
    parts = proxy_str.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{user}:{password}@{host}:{port}"

    # host:port
    if len(parts) == 2:
        return "http://" + proxy_str

    # fallback
    return "http://" + proxy_str

def get_random_proxy():
    proxies = load_proxies()
    if not proxies:
        return None
    chosen = random.choice(proxies)
    proxy_url = format_proxy(chosen)
    return {
        "http": proxy_url,
        "https": proxy_url
    }

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        hcaptcha = data.get("hcaptcha")

        if not username or not password or not hcaptcha:
            return jsonify({"error": "Missing username, password or captcha token"}), 400

        proxy = get_random_proxy()
        if not proxy:
            return jsonify({"error": "No proxies found in proxiesyeah.txt"}), 500

        payload = {
            "username": username,
            "birthday": "01-2000",
            "hcaptcha": hcaptcha,
            "password": password
        }

        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "Referer": "https://codetorch.net/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
        }

        res = requests.post(
            "https://api.codetorch.net/v1/auth/register",
            json=payload,
            headers=headers,
            proxies=proxy,
            timeout=30
        )

        # Save access token to txt file if response is successful
        if res.ok:
            try:
                res_json = res.json()
                # Looks for "access_token" or "token" in the JSON response
                access_token = res_json.get("access_token") or res_json.get("token")
                if access_token:
                    with open(TOKEN_FILE, "a", encoding="utf-8") as f:
                        f.write(access_token + "\n")
            except Exception:
                pass

        return Response(
            res.text,
            status=res.status_code,
            content_type=res.headers.get("Content-Type", "application/json")
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Register with hCaptcha</title>
  <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      background: #f0f2f5;
    }
    .container {
      background: white;
      padding: 2rem;
      border-radius: 12px;
      box-shadow: 0 4px 24px rgba(0,0,0,0.1);
      width: 100%;
      max-width: 420px;
    }
    h1 { margin: 0 0 1.5rem; font-size: 1.35rem; text-align: center; }
    label {
      display: block;
      margin-bottom: 0.35rem;
      font-size: 0.9rem;
      font-weight: 500;
    }
    .input-row {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .input-row input {
      flex: 1;
      margin-bottom: 0;
    }
    input {
      width: 100%;
      padding: 0.65rem 0.8rem;
      margin-bottom: 1rem;
      border: 1px solid #ccc;
      border-radius: 6px;
      font-size: 1rem;
    }
    input:focus {
      outline: none;
      border-color: #1a73e8;
      box-shadow: 0 0 0 3px rgba(26,115,232,0.15);
    }
    .gen-btn {
      padding: 0 0.9rem;
      background: #e8f0fe;
      color: #1a73e8;
      border: 1px solid #c2d7f7;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
    }
    .gen-btn:hover { background: #d2e3fc; }
    .h-captcha {
      margin: 1rem 0;
      display: flex;
      justify-content: center;
    }
    button#registerBtn {
      width: 100%;
      padding: 0.8rem;
      font-size: 1rem;
      font-weight: 600;
      background: #1a73e8;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      margin-top: 0.5rem;
    }
    button#registerBtn:hover { background: #1557b0; }
    button#registerBtn:disabled {
      background: #9bbff0;
      cursor: not-allowed;
    }
    #status {
      margin-top: 1.25rem;
      padding: 0.75rem;
      border-radius: 6px;
      font-size: 0.9rem;
      word-break: break-word;
      white-space: pre-wrap;
      display: none;
    }
    #status.success { background: #e6f4ea; color: #137333; display: block; }
    #status.error   { background: #fce8e6; color: #c5221f; display: block; }
    #status.info    { background: #e8f0fe; color: #1a73e8; display: block; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Create Account</h1>

    <label for="username">Username</label>
    <div class="input-row">
      <input type="text" id="username" placeholder="e.g. fzCameronkei4Bri990" autocomplete="username">
      <button type="button" class="gen-btn" onclick="generateUsername()">Generate</button>
    </div>

    <label for="password">Password</label>
    <input type="password" id="password" placeholder="Your password" autocomplete="new-password">

    <div class="h-captcha"
         data-sitekey="a8c2e5e8-ed06-4773-a963-d89c1926e64a"
         data-callback="onCaptchaSuccess"
         data-error-callback="onCaptchaError"
         data-expired-callback="onCaptchaExpired">
    </div>

    <button id="registerBtn" onclick="register()" disabled>Register Account</button>

    <div id="status"></div>
  </div>

  <script>
    const CHARSET = '1234567890qwertyuiopasdfghjklzxcvbnm';

    function randChar() {
      return CHARSET[Math.floor(Math.random() * CHARSET.length)];
    }

    function randString(len) {
      let s = '';
      for (let i = 0; i < len; i++) s += randChar();
      return s;
    }

    function generateName() {
      return randString(20)
    }

    function generateUsername() {
      document.getElementById('username').value = generateName();
    }

    let captchaToken = null;

    function onCaptchaSuccess(token) {
      captchaToken = token;
      document.getElementById('registerBtn').disabled = false;
      showStatus('Captcha solved – ready to register', 'info');
    }

    function onCaptchaError() {
      captchaToken = null;
      document.getElementById('registerBtn').disabled = true;
      showStatus('Captcha error – please try again', 'error');
    }

    function onCaptchaExpired() {
      captchaToken = null;
      document.getElementById('registerBtn').disabled = true;
      showStatus('Captcha expired – please solve again', 'error');
    }

    function showStatus(msg, type) {
      const el = document.getElementById('status');
      el.textContent = msg;
      el.className = type;
    }

    function resetCaptcha() {
      captchaToken = null;
      document.getElementById('registerBtn').disabled = true;
      if (window.hcaptcha) hcaptcha.reset();
    }

    async function register() {
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;

      if (!username) return showStatus('Please enter a username', 'error');
      if (!password) return showStatus('Please enter a password', 'error');
      if (!captchaToken) return showStatus('Please solve the captcha first', 'error');

      const btn = document.getElementById('registerBtn');
      btn.disabled = true;
      btn.textContent = 'Registering…';
      showStatus('Sending registration request…', 'info');

      try {
        const res = await fetch('/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username,
            password,
            hcaptcha: captchaToken
          })
        });

        const text = await res.text();
        let data;
        try { data = JSON.parse(text); } catch { data = text; }

        if (res.ok) {
          showStatus('Success!\\n' + JSON.stringify(data, null, 2), 'success');
        } else {
          showStatus('Error ' + res.status + ':\\n' + (typeof data === 'string' ? data : JSON.stringify(data, null, 2)), 'error');
        }
      } catch (err) {
        showStatus('Request failed: ' + err.message, 'error');
      } finally {
        resetCaptcha();
        btn.textContent = 'Register Account';
      }
    }
  </script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)