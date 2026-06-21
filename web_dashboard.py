from flask import Flask, render_template_string, request, redirect, session, jsonify
import config
import os
from logger import log_info, log_error
from supabase_client import get_tokens, update_tokens, get_webhooks, update_webhooks

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")

# ===== HTML مع تصميم متجاوب =====
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Nebula - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0d0d1a;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .box {
            background: #16213e;
            padding: 40px 30px;
            border-radius: 16px;
            color: white;
            width: 100%;
            max-width: 380px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
            border: 1px solid #1f3a6e;
        }
        .box h2 {
            text-align: center;
            margin-bottom: 25px;
            font-size: 24px;
            font-weight: 600;
            color: #00bfff;
        }
        .box input {
            width: 100%;
            padding: 12px 16px;
            margin: 10px 0 20px;
            border-radius: 8px;
            border: none;
            background: #1a2a4a;
            color: white;
            font-size: 16px;
            outline: none;
            transition: 0.3s;
        }
        .box input:focus {
            background: #1f3460;
            box-shadow: 0 0 0 2px #00bfff;
        }
        .box button {
            width: 100%;
            padding: 12px;
            background: #00bfff;
            color: #0d0d1a;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
        }
        .box button:hover { background: #00a0d4; transform: translateY(-2px); }
        .error { color: #ff6b6b; text-align: center; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🔐 تسجيل الدخول</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول</button>
        </form>
        {% if error %}
        <p class="error">❌ {{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Nebula - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0d0d1a;
            color: white;
            padding: 16px;
            min-height: 100vh;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: #16213e;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            border: 1px solid #1f3a6e;
        }
        h1 {
            font-size: 24px;
            color: #00bfff;
            text-align: center;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .status-bar {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            background: #0f2040;
            padding: 14px 18px;
            border-radius: 10px;
            margin-bottom: 20px;
            gap: 10px;
            font-size: 14px;
        }
        .status-bar span { background: #1a2a4a; padding: 4px 12px; border-radius: 20px; }
        .section {
            background: #0f2040;
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .section h3 {
            font-size: 18px;
            margin-bottom: 12px;
            color: #00bfff;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .input-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0;
        }
        .input-group input {
            flex: 1;
            min-width: 200px;
            padding: 10px 14px;
            border-radius: 8px;
            border: none;
            background: #1a2a4a;
            color: white;
            font-size: 14px;
            outline: none;
            transition: 0.3s;
        }
        .input-group input:focus { background: #1f3460; box-shadow: 0 0 0 2px #00bfff; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
            font-size: 14px;
        }
        .btn-primary { background: #00bfff; color: #0d0d1a; }
        .btn-primary:hover { background: #00a0d4; transform: translateY(-2px); }
        .btn-danger { background: #ff4444; color: white; }
        .btn-danger:hover { background: #cc3333; transform: translateY(-2px); }
        .btn-success { background: #00ff7f; color: #0d0d1a; }
        .btn-success:hover { background: #00cc66; transform: translateY(-2px); }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 14px;
        }
        th, td {
            padding: 10px 8px;
            text-align: left;
            border-bottom: 1px solid #1f3a6e;
        }
        th { background: #1a2a4a; color: #00bfff; font-weight: 600; }
        .online { color: #00ff7f; font-weight: 600; }
        .offline { color: #ff4444; font-weight: 600; }
        .webhook-status { font-size: 14px; color: #aaa; margin-top: 8px; }
        .webhook-status .ok { color: #00ff7f; }
        .webhook-status .no { color: #ff6b6b; }
        .footer {
            text-align: center;
            color: #666;
            font-size: 13px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #1f3a6e;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }
        .footer a { color: #ff4444; text-decoration: none; font-weight: 600; }
        .footer a:hover { text-decoration: underline; }
        @media (max-width: 600px) {
            .container { padding: 12px; }
            h1 { font-size: 20px; }
            .status-bar { font-size: 12px; padding: 10px; }
            table { font-size: 12px; }
            th, td { padding: 6px 4px; }
            .btn { font-size: 12px; padding: 8px 14px; }
            .input-group input { font-size: 13px; padding: 8px 12px; }
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #00ff7f;
            color: #0d0d1a;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0,255,127,0.3);
            opacity: 0;
            transform: translateY(20px);
            transition: 0.4s ease;
            pointer-events: none;
            z-index: 999;
            max-width: 90%;
        }
        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }
        .toast.error { background: #ff4444; color: white; box-shadow: 0 4px 20px rgba(255,68,68,0.3); }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Nebula - لوحة التحكم</h1>
        <div class="status-bar">
            <span>📋 عدد التوكنات: <strong id="tokenCount">{{ tokens|length }}</strong></span>
            <span>🟢 شغال: <strong id="onlineCount">{{ online }}</strong></span>
            <span>🔴 معطل: <strong id="offlineCount">{{ offline }}</strong></span>
            <span>🔄 <a href="#" onclick="refreshData()" style="color:#00bfff;">تحديث</a></span>
        </div>

        <!-- إدارة التوكنات -->
        <div class="section">
            <h3>➕ إدارة التوكنات</h3>
            <form id="addTokenForm" onsubmit="addToken(event)" class="input-group">
                <input type="text" id="newToken" placeholder="ضع التوكن هنا" required>
                <button type="submit" class="btn btn-primary">إضافة</button>
            </form>
            <div style="overflow-x: auto;">
                <table>
                    <tr>
                        <th>#</th>
                        <th>الحساب</th>
                        <th>الحالة</th>
                        <th>الإجراء</th>
                    </tr>
                    {% for t in tokens %}
                    <tr id="token-row-{{ loop.index }}">
                        <td>{{ loop.index }}</td>
                        <td><strong>{{ t.username or t.token[:20] + '...' }}</strong></td>
                        <td class="{% if t.status == 'online' %}online{% else %}offline{% endif %}">
                            {{ '🟢 شغال' if t.status == 'online' else '🔴 معطل' }}
                        </td>
                        <td>
                            <button onclick="deleteToken('{{ t.token }}')" class="btn btn-danger" style="padding:4px 12px;">🗑️</button>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <!-- إدارة ويب هوك -->
        <div class="section">
            <h3>🔗 إدارة ويب هوك</h3>
            <form id="webhookForm" onsubmit="updateWebhooks(event)" class="input-group">
                <input type="url" id="webhookUrl" placeholder="رابط ويب هوك الإشعارات" value="{{ webhook_url }}">
                <input type="url" id="logWebhookUrl" placeholder="رابط ويب هوك السجلات" value="{{ log_webhook_url }}">
                <button type="submit" class="btn btn-success">تحديث</button>
            </form>
            <div class="webhook-status">
                📌 ويب هوك الإشعارات: 
                <span class="{% if webhook_url %}ok{% else %}no{% endif %}">
                    {% if webhook_url %} ✅ مضبوط {% else %} ❌ غير مضبوط {% endif %}
                </span>
                &nbsp;|&nbsp;
                📋 ويب هوك السجلات: 
                <span class="{% if log_webhook_url %}ok{% else %}no{% endif %}">
                    {% if log_webhook_url %} ✅ مضبوط {% else %} ❌ غير مضبوط {% endif %}
                </span>
            </div>
        </div>

        <!-- معلومات إضافية -->
        <div class="footer">
            <span>⏳ آخر تحديث: <span id="lastUpdate">{{ last_update }}</span></span>
            <a href="/logout">🚪 تسجيل الخروج</a>
        </div>
    </div>

    <!-- Toast Notification -->
    <div id="toast" class="toast"></div>

    <script>
        function showToast(msg, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = 'toast' + (isError ? ' error' : '');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        async function refreshData() {
            showToast('🔄 جاري التحديث...');
            try {
                const resp = await fetch('/api/dashboard_data');
                const data = await resp.json();
                document.getElementById('tokenCount').textContent = data.tokens.length;
                document.getElementById('onlineCount').textContent = data.online;
                document.getElementById('offlineCount').textContent = data.offline;
                document.getElementById('lastUpdate').textContent = data.last_update;
                // تحديث الجدول
                const table = document.querySelector('table');
                let html = `<tr><th>#</th><th>الحساب</th><th>الحالة</th><th>الإجراء</th></tr>`;
                data.tokens.forEach((t, i) => {
                    const statusClass = t.status === 'online' ? 'online' : 'offline';
                    const statusText = t.status === 'online' ? '🟢 شغال' : '🔴 معطل';
                    const username = t.username || t.token.substring(0,20) + '...';
                    html += `<tr id="token-row-${i+1}">
                        <td>${i+1}</td>
                        <td><strong>${username}</strong></td>
                        <td class="${statusClass}">${statusText}</td>
                        <td><button onclick="deleteToken('${t.token}')" class="btn btn-danger" style="padding:4px 12px;">🗑️</button></td>
                    </tr>`;
                });
                table.innerHTML = html;
                showToast('✅ تم التحديث');
            } catch(e) {
                showToast('❌ فشل التحديث', true);
            }
        }

        async function addToken(e) {
            e.preventDefault();
            const input = document.getElementById('newToken');
            const token = input.value.trim();
            if (!token) return;
            const formData = new FormData();
            formData.append('new_token', token);
            try {
                const resp = await fetch('/add_token', { method: 'POST', body: formData });
                if (resp.ok) {
                    showToast('✅ تم إضافة التوكن');
                    input.value = '';
                    setTimeout(refreshData, 500);
                } else {
                    showToast('❌ فشل إضافة التوكن', true);
                }
            } catch(e) {
                showToast('❌ خطأ في الاتصال', true);
            }
        }

        async function deleteToken(token) {
            if (!confirm('هل أنت متأكد من حذف هذا التوكن؟')) return;
            const formData = new FormData();
            formData.append('token', token);
            try {
                const resp = await fetch('/delete_token', { method: 'POST', body: formData });
                if (resp.ok) {
                    showToast('✅ تم حذف التوكن');
                    setTimeout(refreshData, 500);
                } else {
                    showToast('❌ فشل حذف التوكن', true);
                }
            } catch(e) {
                showToast('❌ خطأ في الاتصال', true);
            }
        }

        async function updateWebhooks(e) {
            e.preventDefault();
            const webhook = document.getElementById('webhookUrl').value.trim();
            const logWebhook = document.getElementById('logWebhookUrl').value.trim();
            const formData = new FormData();
            formData.append('webhook_url', webhook);
            formData.append('log_webhook_url', logWebhook);
            try {
                const resp = await fetch('/update_webhooks', { method: 'POST', body: formData });
                if (resp.ok) {
                    showToast('✅ تم تحديث الويب هوك');
                    setTimeout(refreshData, 500);
                } else {
                    showToast('❌ فشل تحديث الويب هوك', true);
                }
            } catch(e) {
                showToast('❌ خطأ في الاتصال', true);
            }
        }
    </script>
</body>
</html>
"""

# ===== دوال API =====
def get_tokens_status():
    tokens = get_tokens()
    results = []
    import requests
    for token in tokens:
        try:
            resp = requests.get(
                "https://discord.com/api/v9/users/@me",
                headers={"Authorization": token},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                results.append({"token": token, "username": data.get("username", "Unknown"), "status": "online"})
            else:
                results.append({"token": token, "username": None, "status": "offline"})
        except:
            results.append({"token": token, "username": None, "status": "offline"})
    return results

def setup_dashboard(app):
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey123")

    @app.route('/dashboard', methods=['GET'])
    def dashboard():
        if not session.get('logged_in'):
            return redirect('/login')
        tokens = get_tokens_status()
        online = sum(1 for t in tokens if t['status'] == 'online')
        offline = len(tokens) - online
        webhooks = get_webhooks()
        from datetime import datetime
        return render_template_string(
            HTML_DASHBOARD,
            tokens=tokens,
            online=online,
            offline=offline,
            webhook_url=webhooks.get("webhook_url", ""),
            log_webhook_url=webhooks.get("log_webhook_url", ""),
            last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    @app.route('/api/dashboard_data', methods=['GET'])
    def dashboard_data():
        if not session.get('logged_in'):
            return jsonify({"error": "Unauthorized"}), 401
        tokens = get_tokens_status()
        online = sum(1 for t in tokens if t['status'] == 'online')
        offline = len(tokens) - online
        from datetime import datetime
        return jsonify({
            "tokens": tokens,
            "online": online,
            "offline": offline,
            "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            if request.form.get('password') == DASHBOARD_PASSWORD:
                session['logged_in'] = True
                return redirect('/dashboard')
            return render_template_string(HTML_LOGIN, error="❌ كلمة المرور غير صحيحة")
        return render_template_string(HTML_LOGIN, error=None)

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        return redirect('/login')

    @app.route('/add_token', methods=['POST'])
    def add_token():
        if not session.get('logged_in'):
            return redirect('/login')
        new_token = request.form.get('new_token')
        if new_token:
            tokens = get_tokens()
            if new_token not in tokens:
                tokens.append(new_token)
                update_tokens(tokens)
                log_info(f"➕ تم إضافة توكن جديد: {new_token[:15]}...")
        return redirect('/dashboard')

    @app.route('/delete_token', methods=['POST'])
    def delete_token():
        if not session.get('logged_in'):
            return redirect('/login')
        token = request.form.get('token')
        tokens = get_tokens()
        if token in tokens:
            tokens.remove(token)
            update_tokens(tokens)
            log_info(f"🗑️ تم حذف توكن: {token[:15]}...")
        return redirect('/dashboard')

    @app.route('/update_webhooks', methods=['POST'])
    def update_webhooks_route():
        if not session.get('logged_in'):
            return redirect('/login')
        webhook_url = request.form.get('webhook_url', '').strip()
        log_webhook_url = request.form.get('log_webhook_url', '').strip()
        update_webhooks(webhook_url, log_webhook_url)
        log_info(f"🔗 تم تحديث ويب هوك: {webhook_url[:30]}...")
        return redirect('/dashboard')