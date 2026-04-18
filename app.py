import os
import io
import qrcode
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

# Тимчасова база даних у пам'яті (RAM)
storage = {}

# --- 1. ГОЛОВНА СТОРІНКА (Форма для реєстрації речі) ---
@app.route('/')
def index():
    return render_template_string('''
        <body style="font-family: sans-serif; max-width: 500px; margin: 40px auto; padding: 20px;">
            <h1>📦 QR-Found: Створи свій код</h1>
            <p>Заповни дані, щоб ми могли повернути тобі річ!</p>
            <form action="/create" method="POST" style="display: flex; flex-direction: column; gap: 10px;">
                <input type="text" name="item_name" placeholder="Що це за річ? (напр. Ключі)" required>
                <input type="text" name="owner_name" placeholder="Твоє ім'я" required>
                <input type="email" name="email" placeholder="Твій Email" required>
                <input type="text" name="phone" placeholder="Твій телефон" required>
                <input type="text" name="telegram" placeholder="Нік у Telegram (без @)" required>
                <button type="submit" style="background: #007bff; color: white; border: none; padding: 10px; cursor: pointer;">
                    Згенерувати QR код
                </button>
            </form>
            <hr>
        </body>
    ''')

# --- 2. СТВОРЕННЯ (Запис у базу та показ результату) ---
@app.route('/create', methods=['POST'])
def create_item():
    item_id = str(len(storage) + 1)
    
    # Зберігаємо всі твої поля
    storage[item_id] = {
        "item_name": request.form.get('item_name'),
        "owner_name": request.form.get('owner_name'),
        "email": request.form.get('email'),
        "phone": request.form.get('phone'),
        "telegram": request.form.get('telegram')
    }
    
    return render_template_string(f'''
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>Готово, {storage[item_id]['owner_name']}!</h1>
            <p>Твій QR-код для: <b>{storage[item_id]['item_name']}</b></p>
            <img src="/generate_qr/{item_id}" style="border: 5px solid white; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <br><br>
            <p>Скачай це фото, роздрукуй та наклей на річ.</p>
            <a href="/">← Створити ще один</a>
        </body>
    ''')

# --- 3. СТОРІНКА ЗНАХІДЦЯ (Те, що відкриється по QR) ---
@app.route('/item/<item_id>')
def view_item(item_id):
    data = storage.get(item_id)
    if not data:
        return "<h1>Річ не знайдена 404</h1>", 404
    
    return render_template_string(f'''
        <body style="font-family: sans-serif; padding: 20px; background: #f8f9fa;">
            <div style="max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h1 style="color: #28a745;">Знайдено річ! 🔍</h1>
                <p>Ви щойно відсканували QR-код на речі: <b>{data['item_name']}</b></p>
                <hr>
                <h3>Контакти власника ({data['owner_name']}):</h3>
                <p>📞 <b>Телефон:</b> {data['phone']}</p>
                <p>📧 <b>Email:</b> {data['email']}</p>
                <p>✈️ <b>Telegram:</b> <a href="https://t.me/{data['telegram']}">@{data['telegram']}</a></p>
                <br>
                <p style="font-style: italic; color: #666;">Дякуємо, що допомагаєте речам повертатися додому!</p>
            </div>
        </body>
    ''')

# --- 4. ТЕХНІЧНА ГЕНЕРАЦІЯ КАРТИНКИ ---
@app.route('/generate_qr/<item_id>')
def generate_qr(item_id):
    qr_url = f"https://qr-found.onrender.com/item/{item_id}"
    img = qrcode.make(qr_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)