from flask import Flask, render_template_string, request, redirect, session, jsonify
import config
import os
from logger import log_info, log_error
from supabase_client import get_tokens, update_tokens, get_webhooks, update_webhooks

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>🔐 Nebula - Login</title>
    <style>
        body { font-family: Arial; background: #1a1a2e; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .box { background: #16213e; padding: 30px; border-radius: 10px; color: white; width: 300px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
        button { width: 100%; padding: 10px; background: #0f3460; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #1a4a7a; }
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
        <p style="color: red;">❌ {{ error }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>📊 Nebula - Dashboard</title>
    <style>
        body { font-family: Arial; background: #1a1a2e; color: white; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #16213e; padding: 20px; border-radius: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; border-bottom: 1px solid #333; text-align: left; }
        th { background: #0f3460; }
        .online { color: #00ff7f; }
        .offline { color: #ff4444; }
        .input-group { display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap; }
        .input-group input { flex: 1; padding: 10px; border-radius: 5px; border: none; min-width: 200px; }
        .btn { padding: 10px 20px; background: #0f3460; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #1a4a7a; }
        .btn-danger { background: #ff4444; }
        .btn-danger:hover { background: #cc3333; }
        .status-bar { display: flex; justify-content: space-between; background: #0f3460; padding: 10px; border-radius: 5px; flex-wrap: wrap; }
        .section { background: #0f3460; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .section h3 { margin-top: 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Nebula - لوحة التحكم</h1>
        <div class="status-bar">
            <span>📋 عدد التوكنات: <strong>{{ tokens|length }}</strong></span>
            <span>🟢 شغال: <strong>{{ online }}</strong></span>
            <span>🔴 معطل: <strong>{{ offline }}</strong></span>
            <span>🔄 <a href="/dashboard" style="color: #00bfff;">تحديث</a></span>
        </div>

        <!-- إدارة التوكنات -->
        <div class="section">
            <h3>➕ إدارة التوكنات</h3>
            <form method="POST" action="/add_token" class="input-group">
                <input type="text" name="new_token" placeholder="ضع التوكن هنا" required>
                <button type="submit" class="btn">إضافة</button>
            </form>
            <table>
                <tr>
                    <th>#</th>
                    <th>الحساب</th>
                    <th>الحالة</th>
                    <th>الإجراء</th>
                </tr>
                {% for t in tokens %}
                <tr>
                    <td>{{ loop.index }}</td>
                    <td>{{ t.username or t.token[:20] + '...' }}</td>
                    <td class="{% if t.status == 'online' %}online{% else %}offline{% endif %}">
                        {{ '🟢 شغال' if t.status == 'online' else '🔴 معطل' }}
                    </td>
                    <td>
                        <form method="POST" action="/delete_token" style="display:inline;">
                            <input type="hidden" name="token" value="{{ t.token }}">
                            <button type="submit" class="btn btn-danger">🗑️</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <!-- إدارة ويب هوك -->
        <div class="section">
            <h3>🔗 إدارة ويب هوك</h3>
            <form method="POST" action="/update_webhooks">
                <div class="input-group">
                    <input type="url" name="webhook_url" placeholder="رابط ويب هوك الإشعارات" value="{{ webhook_url }}">
                    <input type="url" name="log_webhook_url" placeholder="رابط ويب هوك السجلات" value="{{ log_webhook_url }}">
                    <button type="submit" class="btn">تحديث</button>
                </div>
            </form>
            <p style="color: #888; font-size: 14px;">
                📌 الويب هوك الحالي: 
                {% if webhook_url %} ✅ مضبوط {% else %} ❌ غير مضبوط {% endif %}
                &nbsp;|&nbsp;
                📋 سجلات: 
                {% if log_webhook_url %} ✅ مضبوط {% else %} ❌ غير مضبوط {% endif %}
            </p>
        </div>

        <p style="color: #888; margin-top: 20px;">
            ⏳ آخر تحديث: {{ last_update }}
        </p>
        <a href="/logout" style="color: #ff4444;">🚪 تسجيل الخروج</a>
    </div>
</body>
</html>
"""

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
                results.append({
                    "token": token,
                    "username": data.get("username", "Unknown"),
                    "status": "online"
                })
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