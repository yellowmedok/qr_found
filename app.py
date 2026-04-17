import os
from flask import Flask, request, jsonify

app = Flask(__name__)

storage = {}

@app.route('/')
def home():
    return "Сервер QR-Found працює! Команда PP-34 готова до захисту."

@app.route('/create', methods=['POST'])
def create_item():
    data = request.json
    item_id = str(len(storage) + 1)
    storage[item_id] = {
        "item_name": data['item_name'],
        "owner_name": data['owner_name'],
        "contact": data['contact'],
        "finder_message": None
    }
    # Заміни 'qr-found.onrender.com' на своє реальне посилання з Render
    return jsonify({"qr_link": f"https://qr-found.onrender.com/item/{item_id}"})

@app.route('/item/<item_id>', methods=['GET'])
def view_item(item_id):
    item = storage.get(item_id)
    if not item:
        return "Річ не знайдена", 404
    return f"Ви знайшли річ: {item['item_name']}. Будь ласка, залиште свій номер телефону."

if __name__ == '__main__':
    # Отримуємо порт, який нам виділяє Render
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' робить сервер видимим для Render
    app.run(host='0.0.0.0', port=port)