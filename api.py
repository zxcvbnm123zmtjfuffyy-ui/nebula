from flask import Flask, jsonify, request
from supabase_client import get_all_accounts
from logger import log_info, log_error

app = Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    data = get_all_accounts()
    return jsonify(data)

@app.route('/check/<user_id>', methods=['GET'])
def check_account(user_id):
    data = get_all_accounts()
    for acc in data:
        if acc.get('user_id') == user_id:
            return jsonify(acc)
    return jsonify({"error": "الحساب غير موجود"}), 404

@app.route('/nitro', methods=['GET'])
def nitro():
    data = get_all_accounts()
    return jsonify(data)

@app.route('/next', methods=['GET'])
def next_account():
    data = get_all_accounts()
    ready = [a for a in data if a.get('boost_status') == 'ready']
    if ready:
        return jsonify(ready)
    waiting = [a for a in data if a.get('boost_status') == 'waiting' and a.get('cooldown_ends_at')]
    if waiting:
        # نرتب حسب أقرب وقت انتهاء
        waiting.sort(key=lambda x: x.get('cooldown_ends_at', ''))
        return jsonify(waiting[0])
    return jsonify({"error": "لا توجد بيانات"}), 404

@app.route('/pause', methods=['POST'])
def pause():
    # سيتم تنفيذها عبر main مع scheduler
    return jsonify({"status": "paused"})

@app.route('/resume', methods=['POST'])
def resume():
    return jsonify({"status": "resumed"})

def run_api():
    app.run(host='0.0.0.0', port=5000, use_reloader=False)