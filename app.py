import os
import io
import qrcode
import base64
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request, render_template_string, send_file, url_for
app = Flask(__name__)

# Тимчасове сховище даних
storage = {}

COMMON_STYLES = '''
:root {
    --color-bg: #DEE7E5;
    --color-dark: #373636;
    --color-primary: #0E7156;
    --color-accent: #D9F7EE;
    --color-text: #444;
    --font-main: 'Baloo 2', sans-serif;
    --font-logo: 'Baloo Bhaina 2', cursive;
    --shadow-main: 0 10px 25px rgba(0,0,0,0.1);
}
* { box-sizing: border-box; }
body {
    margin: 0;
    background: var(--color-bg);
    font-family: var(--font-main);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    overflow-x: hidden; 
}
.main-header {
    width: 100%;
    height: 70px;
    background: var(--color-dark);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    z-index: 1000;
}
.header-inner {
    width: 100%;
    max-width: 420px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.header-logo-img {
    width: 90px;
    cursor: pointer;
}
'''
#хедер
HEADER_HTML = '''
    <header class="main-header">
        <div class="header-inner">
            <a href="/">
                <a href="/"><img src="{{ url_for('static', filename='logo.png') }}" style="width: 90px;"></a>
            </a>
        </div>
    </header>
'''

#футер
FOOTER_HTML = '''
    <footer class="main-footer">
        <div class="footer-inner">
            <div>© 2026 QR-Found</div>
            <a href="/faq" class="footer-link">FAQ</a>
        </div>
    </footer>
'''
FOOTER_STYLE = '''
.main-footer {
    width: 100%;
    min-height: 80px;
    background: var(--color-dark);
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: auto;
    padding: 20px 0;
}
.footer-inner {
    color: var(--color-accent);
    font-size: 14px;
    text-align: center;
}
.footer-link {
    color: white;
    text-decoration: none;
    display: inline-block;
    margin-top: 8px;
    background: rgba(255,255,255,0.1);
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: 600;
    transition: background 0.3s;
}
.footer-link:hover {
    background: var(--color-primary);
}
'''

# кнопка назад
BACK_BUTTON_HTML = '''
<div class="back-nav">
    <button onclick="history.back()" class="back-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        <span>Back</span>
    </button>
</div>
'''

BACK_BUTTON_STYLE = '''
.back-nav {
    width: 100%;
    max-width: 420px;
    margin: 0 auto;
    padding: 10px 16px 0;
    display: flex;
    height: 0; /* Не займає місця в потоці, щоб не зсувати заголовок */
}
.back-btn {
    background: none;
    border: none;
    color: var(--color-primary);
    display: flex;
    align-items: center;
    gap: 4px;
    font-family: var(--font-main);
    font-weight: 700;
    font-size: 15px; /* Зменшено розмір */
    cursor: pointer;
    padding: 5px 0;
    transition: transform 0.2s;
    position: relative;
    z-index: 10;
}
.back-btn:active { transform: translateX(-3px); }
'''

#кнопка вверх
SCROLL_TOP_HTML = '''
<button id="scrollTopBtn" class="scroll-top-btn" onclick="window.scrollTo({top: 0, behavior: 'smooth'})">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>
</button>
'''

SCROLL_TOP_STYLE = '''
.scroll-top-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 45px;
    height: 45px;
    background: var(--color-primary);
    border-radius: 50%;
    border: none;
    display: none;
    justify-content: center;
    align-items: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    cursor: pointer;
    z-index: 1500;
    transition: opacity 0.3s, transform 0.3s, bottom 0.3s;
}
.scroll-top-btn.visible { display: flex; animation: fadeIn 0.3s; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
'''

SCROLL_SCRIPT = '''
<script>
    const scrollTopBtn = document.getElementById("scrollTopBtn");
    const footer = document.querySelector(".main-footer");

    window.onscroll = function() {
        if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
            scrollTopBtn.classList.add("visible");
        } else {
            scrollTopBtn.classList.remove("visible");
        }

        if (footer) {
            const footerRect = footer.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            if (footerRect.top < windowHeight) {
                const offset = windowHeight - footerRect.top + 20;
                scrollTopBtn.style.bottom = offset + "px";
            } else {
                scrollTopBtn.style.bottom = "20px";
            }
        }
    };
</script>
'''

#головна сторінка
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

<link href="https://fonts.googleapis.com/css2?family=Baloo+Bhaina+2&family=Baloo+2:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://unpkg.com/html5-qrcode"></script>

<style>
''' + COMMON_STYLES + FOOTER_STYLE + SCROLL_TOP_STYLE + '''

.page {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
}

.container {
    width: 100%;
    max-width: 420px;
    padding: 20px 16px 40px; 
    text-align: center;
}

/* TITLE */
.hero-title {
    display: flex;
    font-weight: 800;
    font-size: clamp(32px, 10vw, 52px); 
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin-top: -10px;
}

.qr-icon {
    width: 40px;
}

.logo-big {
    font-family: var(--font-logo);
    color: var(--color-dark);
    text-shadow:
        2px 2px 0 #0E7156,
        2px 2px 5px rgba(14,113,86,0.3);
}

/* KEY */
.hero-image {
    margin: -10px 0 0 0;
}

.big-key {
    width: 100%;
    max-width: 320px;
    height: auto;
    display: block;
    margin: 0 auto;
}

/* TEXT */
.title {
    font-size: 28px;
    font-weight: 700;
    color: var(--color-dark);
}

.title span {
  display: block; 
}

.description {
    font-size: 16px;
    color: var(--color-text);
    margin: 15px 0 25px;
    line-height: 1.4;
}

/* BUTTON */
.btn {
    width: 100%; 
    max-width: 280px; 
    padding: 16px;
    background: var(--color-primary);
    border: none;
    border-radius: 16px;
    color: white;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    margin-bottom: 5px;
    transition: transform 0.1s ease;
    text-align: center;
}

.btn-secondary {
    background: var(--color-accent);
    color: var(--color-primary);
    border: 2px solid var(--color-primary);
}

.btn:active {
    transform: scale(0.96);
}

/* MODAL / OVERLAY */
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 2000;
}

.overlay.active {
    display: flex;
}

.modal {
    width: 92%;
    max-width: 380px;
    background: white;
    border-radius: 20px;
    padding: 20px;
    position: relative;
    max-height: 90vh;
    overflow-y: auto;
}

.close-btn {
    position: absolute;
    right: 15px;
    top: 10px;
    font-size: 24px;
    cursor: pointer;
    color: #999;
}

.modal-info {
    font-size: 15px;
    color: #444;
    margin-bottom: 15px;
    line-height: 1.5;
    text-align: center;
}

/* GRADIENT TITLE */
.gradient-title {
    font-size: 20px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #0E7156, #00c2a8, #0E7156);
    background-size: 200% auto;
    color: transparent;
    -webkit-background-clip: text;
    background-clip: text;
    animation: shine 3s linear infinite;
}

@keyframes shine {
    0% { background-position: 0% center; }
    100% { background-position: 200% center; }
}

input, select {
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
    border: 1px solid #ddd;
    font-family: inherit;
    font-size: 16px; 
}

                                  
/* PHONE ROW FIX */
.phone-row {
    display: flex;
    gap: 10px;
    align-items: center;
}

.phone-code {
    width: 110px;
}

.phone-input {
    flex: 1;
}

/* STEPS */
.how-title {
    font-size: 26px;
    font-weight: 800;
    text-align: center;
    margin: 20px 0 20px;
    color: var(--color-dark);
}

.steps {
    width: 100%;
    max-width: 420px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    padding: 0 16px 20px;
}

.step {
    background: white;
    border-radius: 18px;
    padding: 15px;
    box-shadow: var(--shadow-main);
    text-align: center;
}

.step img {
    width: 100%;
    max-width: 100px;
    height: auto;
}

.step-number {
    font-weight: 800;
    font-size: 18px;
    color: var(--color-primary);
    margin-top: 8px;
}

.step-text {
    font-size: 14px;
    color: var(--color-text);
    margin-top: 5px;
}

.motivation-text {
    max-width: 380px;
    margin: 0 auto 60px;
    padding: 0 16px;
    font-size: 18px;
    font-weight: 700;
    color: var(--color-primary);
    line-height: 1.4;
    text-align: center; 
}

#reader {
    width: 100%;
    border-radius: 15px;
    overflow: hidden;
    border: 2px solid var(--color-primary) !important;
}

''' + FOOTER_STYLE + SCROLL_TOP_STYLE + '''
</style>
</head>

<body>

    ''' + HEADER_HTML + '''

<div class="page">
    <div class="container">
        <div class="hero-title">
            <img src="{{ url_for('static', filename='qr-logo.png') }}" class="qr-icon">
            <div class="logo-big">QR-Found</div>
        </div>

        <div class="hero-image">
            <img src="{{ url_for('static', filename='big-key.png') }}" class="big-key">
        </div>

        <div class="title">Lost & Found <span>Smart QR System</span></div>

        <div class="description">
            Create a smart digital tag that helps people return your lost items by contacting you instantly through QR scanning.
        </div>

        <button class="btn" onclick="openModal()">Create QR-code</button>
        <button class="btn btn-secondary" onclick="openScanner()">Scan QR-code</button>
    </div>

    <div class="overlay" id="overlay">
        <div class="modal">
            <div class="close-btn" onclick="closeModal()">✕</div>
            <div class="modal-info">
                <div class="gradient-title">Create your QR code</div>
                Fill in a few simple details so your item can be returned to you if it gets lost.  
                This information helps the finder contact you quickly and safely.
            </div>
            <form action="/create" method="POST">
                <input type="text" name="item_name" placeholder="What is your item? (english)" required
                       pattern="[A-Za-z\s]+" 
                       title="Please use English letters only"
                       onkeypress="return /[a-z]/i.test(event.key)"
                       oninvalid="this.setCustomValidity('Please use English letters only')" 
                       oninput="this.setCustomValidity('')">             
                <input type="text" name="owner_name" placeholder="Your name (english)" required
                       pattern="[A-Za-z\s]+" 
                       title="Please use English letters only"
                       onkeypress="return /[a-z]/i.test(event.key)"
                       oninvalid="this.setCustomValidity('Please enter your name in English')" 
                       oninput="this.setCustomValidity('')">
                <div class="phone-row">
                    <select name="country_code" class="phone-code">
                        <option value="+380">🇺🇦 +380</option>
                        <option value="+48">🇵🇱 +48</option>
                        <option value="+49">🇩🇪 +49</option>
                        <option value="+1">🇺🇸 +1</option>
                        <option value="+44">🇬🇧 +44</option>
                    </select>
                    <input type="tel" name="phone" class="phone-input" placeholder="Phone" required 
                           maxlength="9"
                           oninput="this.value = this.value.replace(/[^0-9]/g, '').substring(0, 9); this.setCustomValidity('')"
                           oninvalid="this.setCustomValidity('Please enter 9 digits')" >
                </div>

                <input type="email" name="email" placeholder="Email address" required
                       oninvalid="this.setCustomValidity('Please enter a valid email')" oninput="this.setCustomValidity('')">
                
                <input type="text" name="telegram" placeholder="@telegram username" required
                       oninvalid="this.setCustomValidity('Please enter your Telegram')" oninput="this.setCustomValidity('')">

                <button class="btn" type="submit" style="width:100%; max-width:100%; margin-top:10px;">
                    Generate QR Code
                </button>
            </form>
        </div>
    </div>

    <div class="overlay" id="scannerOverlay">
        <div class="modal">
            <div class="close-btn" onclick="closeScanner()">✕</div>
            <div class="gradient-title">Scan QR Code</div>
            <div id="reader"></div>
        </div>
    </div>

    <div class="how-title">How it works?</div>

    <div class="steps">
        <div class="step">
            <img src="{{ url_for('static', filename='step1.png') }}">
            <div class="step-number">1</div>
            <div class="step-text">Create your QR-code</div>
        </div>
        <div class="step">
            <img src="{{ url_for('static', filename='step2.png') }}">
            <div class="step-number">2</div>
            <div class="step-text">Attach it to your item</div>
        </div>
        <div class="step">
            <img src="{{ url_for('static', filename='step3.png') }}">
            <div class="step-number">3</div>
            <div class="step-text">If lost, a finder scans the code</div>
        </div>
        <div class="step">
            <img src="{{ url_for('static', filename='step4.png') }}">
            <div class="step-number">4</div>
            <div class="step-text">They contact you directly</div>
        </div>
    </div>

    <div class="motivation-text">
        Don't wait for things to disappear! <br><br>
        Use our service to create QR codes today and protect as many of your belongings as possible. Safety is just one scan away!
    </div>
</div>

    ''' + FOOTER_HTML + SCROLL_TOP_HTML + '''

<script>
let html5QrCode; //змінна для роботи зі сканером QR

function openModal() {
    document.getElementById("overlay").classList.add("active");
}

function closeModal() {
    document.getElementById("overlay").classList.remove("active");
}

//запускає камеру для сканування QR
function openScanner() {
    document.getElementById("scannerOverlay").classList.add("active");
    html5QrCode = new Html5Qrcode("reader"); //підключає бібліотеку для QR
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };
    html5QrCode.start({ facingMode: "environment" }, config, (decodedText) => { //відкриває задню камеру телефону
        window.location.href = decodedText; // якщо QR знайдено - переходимо по ньому
        closeScanner();
    });
}

function closeScanner() {
    document.getElementById("scannerOverlay").classList.remove("active");
    // якщо камера запущена - зупиняємо її
    if (html5QrCode) {
        html5QrCode.stop().catch(err => console.log(err));
    }
}

window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search); //перевіряє URL
    if (urlParams.get('openModal') === 'true') {
        openModal();
    }
}
</script>
''' + SCROLL_SCRIPT + '''
</body>
</html>
''')

#створення qr
@app.route('/create', methods=['POST'])
def create_item():
    item_id = str(len(storage) + 1) #унікальний ID для кожного предмета
    user_data = request.form.to_dict()
    storage[item_id] = user_data
    
    qr_url = f"{request.host_url}item/{item_id}" #QR містить посилання на сторінку предмета
    img = qrcode.make(qr_url)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link href="https://fonts.googleapis.com/css2?family=Baloo+Bhaina+2&family=Baloo+2:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    
    .container { width: 100%; max-width: 420px; margin: 0 auto; padding: 40px 16px; text-align: center; flex: 1; }
    
    .success-title { color: var(--color-primary); font-size: 28px; font-weight: 800; line-height: 1.2; }
    .sub-title { font-size: 18px; font-weight: 700; color: var(--color-dark); margin-top: 10px; }
    
    .qr-container { background: white; padding: 20px; border-radius: 20px; display: inline-block; margin: 25px 0; box-shadow: var(--shadow-main); width: 100%; max-width: 220px; }
    .qr-img { width: 100%; height: auto; }
    
    .btn { width: 100%; max-width: 280px; padding: 14px; background: var(--color-primary); border: none; border-radius: 16px; color: white; font-size: 18px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-block; margin-bottom: 12px; transition: transform 0.1s; text-align: center; }
    .btn:active { transform: scale(0.96); }
    
    .instruction-list { text-align: left; font-size: 16px; color: var(--color-dark); font-weight: 600; padding: 0; list-style: none; margin: 20px 0; }
    .instruction-list li { margin-bottom: 10px; }
    .warning { color: #d9534f; font-size: 13px; margin: 20px 0; font-weight: 500; line-height: 1.4; }
    '''+ COMMON_STYLES  + FOOTER_STYLE + BACK_BUTTON_STYLE + SCROLL_TOP_STYLE + '''
</style>
</head>
<body>
    
    ''' + HEADER_HTML+ BACK_BUTTON_HTML + '''

    <div class="container">
        <div class="success-title">Thank you, {{ name }}!</div>
        <div class="success-title">Your QR-Found code is ready.</div>
        
        <div class="sub-title">Your Unique QR Code</div>
        
        <div class="qr-container">
            <img src="data:image/png;base64,{{ qr_code }}" class="qr-img">
        </div>

        <a href="/generate_pdf/{{ item_id }}" class="btn">Download PDF</a>
        <a href="/generate_qr/{{ item_id }}?download=png" class="btn">Download PNG</a>

        <ul class="instruction-list">
            <li>1. Print the downloaded PDF.</li>
            <li>2. Attach the tag securely to your item.</li>
        </ul>
        
        <div class="warning">
            This is a temporary page. DO NOT store this QR code on our server. If you close this window without downloading, it WILL BE LOST forever.
        </div>

        <div class="success-title" style="font-size: 24px; margin-bottom: 20px;">Protect another item in just one minute.</div>

        <a href="/?openModal=true" class="btn">Create new QR-code</a>
    </div>
    ''' + FOOTER_HTML + SCROLL_TOP_HTML + SCROLL_SCRIPT + '''
</body>
</html>
    ''', name=user_data['owner_name'], qr_code=qr_base64, item_id=item_id)

#створює pdf для друку qr
@app.route('/generate_pdf/<item_id>')
def generate_pdf(item_id):
    data = storage.get(item_id)
    if not data:
        return "Not found", 404

    qr_url = f"{request.host_url}item/{item_id}"
    img = qrcode.make(qr_url)

    qr_buf = io.BytesIO()
    img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    pdf = FPDF()
    pdf.add_page()

    font_name = "Helvetica"

    # рамка
    pdf.set_draw_color(14, 113, 86)
    pdf.set_line_width(1.5)
    pdf.rect(50, 20, 110, 145)

    # заголовок
    pdf.set_font(font_name, 'B', 26)
    pdf.set_y(32)
    pdf.set_text_color(14, 113, 86)
    pdf.cell(0, 15, "QR-Found", ln=True, align='C')

    # QR 
    pdf.image(qr_buf, x=65, y=52, w=80)

    # текст
    pdf.set_y(138)
    pdf.set_text_color(55, 54, 54)

    pdf.set_font(font_name, 'B', 18)
    pdf.cell(0, 10, f"Item: {data['item_name']}", ln=True, align='C')

    pdf.set_font(font_name, 'B', 11)
    pdf.cell(0, 7, "SCAN TO CONTACT OWNER", ln=True, align='C')

    # правильний output для Render
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    pdf_output = io.BytesIO(pdf_bytes)

    return send_file(
        pdf_output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"QR_Found_{item_id}.pdf"
    )

#створює картинку QR-коду
@app.route('/generate_qr/<item_id>')
def generate_qr(item_id):
    data = storage.get(item_id)
    if not data:
        return "Not found", 404

    qr_url = f"{request.host_url}item/{item_id}"
    qr = qrcode.QRCode(box_size=12, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    # створення qr
    qr_img = qr.make_image(fill_color=(55, 54, 54), back_color="white").convert('RGB')

    canvas = Image.new('RGB', (600, 800), color='white')
    draw = ImageDraw.Draw(canvas)

    # Зелена рамка (14, 113, 86)
    draw.rectangle([40, 40, 560, 760], outline=(14, 113, 86), width=10)

    def get_font(size):
        for f in ["Baloo2-Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]:
            try: return ImageFont.truetype(f, size)
            except: continue
        return ImageFont.load_default()

    # заголовок
    draw.text((300, 110), "QR-Found", fill=(14, 113, 86), font=get_font(70), anchor="mm")

    # розміщення qr
    qr_img = qr_img.resize((420, 420), Image.Resampling.LANCZOS)
    canvas.paste(qr_img, (90, 180))

    item_name = data.get('item_name', 'Item')
    draw.text((300, 650), f"Item: {item_name}", fill=(55, 54, 54), font=get_font(48), anchor="mm")
    draw.text((300, 710), "SCAN TO CONTACT OWNER", fill=(55, 54, 54), font=get_font(28), anchor="mm")

    buf = io.BytesIO()
    canvas.save(buf, format='PNG')
    buf.seek(0)

    if request.args.get('download'):
        return send_file(buf, mimetype='image/png', as_attachment=True, download_name=f"QR_Found_{item_id}.png")
    
    return send_file(buf, mimetype='image/png')

#сторінка, яка відкривається після сканування QR
@app.route('/item/<item_id>')
def item(item_id):
    data = storage.get(item_id)
    if not data:
        return "<h1>Item not found</h1>", 404
        
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>

    .container { width: 100%; max-width: 420px; margin: 0 auto; padding: 40px 24px; text-align: center; flex: 1;}
    
    .found-title { color: var(--color-primary); font-size: 32px; font-weight: 800; margin-bottom: 20px; }
    .hero-text { font-size: 18px; color: var(--color-dark); font-weight: 600; line-height: 1.4; margin-bottom: 40px; }
    
    .info-card { 
        text-align: left; 
        background: white; 
        padding: 25px; 
        border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 40px;
    }
    .info-row { 
        display: flex; 
        margin-bottom: 12px; 
        gap: 10px;
    }
    .info-label { 
        font-size: 18px; 
        font-weight: 700; 
        color: #666; 
        min-width: 70px; 
    }
    .info-value { 
        font-size: 18px; 
        font-weight: 800; 
        color: var(--color-dark); 
        word-break: break-all;
    }

    .btn { width: 100%; max-width: 280px; padding: 16px; background: var(--color-primary); border: none; border-radius: 16px; color: white; font-size: 18px; font-weight: 700; cursor: pointer; text-decoration: none; display: inline-block; margin-bottom: 12px; transition: transform 0.1s; text-align: center; }
    .btn:active { transform: scale(0.96); } 
    .footer-note { font-size: 16px; font-weight: 600; color: var(--color-dark); margin-top: 30px; line-height: 1.4; }
    .protect-box {
        margin-top: 60px;
        padding: 30px 20px;
        background: rgba(14, 113, 86, 0.1);
        border-radius: 25px;
        border: 2px dashed var(--color-primary);
    }
    .protect-title { font-size: 22px; font-weight: 800; color: var(--color-primary); margin-bottom: 10px; }
    .protect-text { font-size: 15px; color: var(--color-dark); margin-bottom: 20px; font-weight: 500; }
    ''' + COMMON_STYLES + FOOTER_STYLE + BACK_BUTTON_STYLE + SCROLL_TOP_STYLE + '''
</style>
</head>
<body>
    
    '''+ HEADER_HTML  + BACK_BUTTON_HTML + '''

    <div class="container">
        <div class="found-title">Found an Item?</div>
        <div class="hero-text">Thank you for being a hero! Here is the owner's contact information.</div>
        
        <div class="info-card">
            <div class="info-row">
                <div class="info-label">Item:</div>
                <div class="info-value">{{ item_name }}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Owner:</div>
                <div class="info-value">{{ owner_name }}</div>
            </div>
            <div class="info-row">
                <div class="info-label">Email:</div>
                <div class="info-value">{{ email }}</div>
            </div>
        </div>

        <a href="tel:{{ full_phone }}" class="btn">Call owner</a>
        <a href="https://t.me/{{ telegram }}" target="_blank" class="btn">Chat on telegram</a>
        
        <div class="footer-note">Your kindness makes the world a better place!</div>

        <div class="protect-box">
            <div class="protect-title">Protect your items too!</div>
            <div class="protect-text">Create your own smart QR tag for your keys, bag or laptop in just 1 minute. It's free and secure.</div>
            <a href="/?openModal=true" class="btn">Create QR-code</a>
        </div>
    </div>
    ''' + FOOTER_HTML + SCROLL_TOP_HTML + SCROLL_SCRIPT + '''
</body>
</html>
    ''', 
    item_name=data['item_name'], 
    owner_name=data['owner_name'], 
    email=data['email'], 
    full_phone=data.get('country_code', '') + data.get('phone', ''),
    telegram=data.get('telegram', '').replace('@', ''))

#faq
@app.route('/faq')
def faq():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        
        .container { width: 100%; max-width: 500px; margin: 0 auto; padding: 40px 20px; flex: 1; }
        
        .faq-title { color: var(--color-dark); font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 30px; }
        
        .accordion-item { background: white; margin-bottom: 10px; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .accordion-header { padding: 18px 20px; font-weight: 700; color: var(--color-dark); cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none; }
        .accordion-header:hover { background: #f9f9f9; }
        .accordion-content { padding: 0 20px; max-height: 0; overflow: hidden; transition: all 0.3s ease-out; color: #555; line-height: 1.6; }
        .accordion-item.active .accordion-content { padding: 10px 20px 20px; max-height: 300px; }
        .accordion-item.active .icon { transform: rotate(180deg); }
        .icon { transition: transform 0.3s; font-weight: bold; color: var(--color-primary); }

        ''' + COMMON_STYLES + FOOTER_STYLE + BACK_BUTTON_STYLE + SCROLL_TOP_STYLE + '''
    </style>
</head>
<body>
    
    ''' + HEADER_HTML + BACK_BUTTON_HTML + '''
    
    <div class="container">
        <h1 class="faq-title">Frequently Asked Questions</h1>
        
        <div class="accordion">
            <div class="accordion-item">
                <div class="accordion-header">Is QR-Found free to use? <span class="icon">▼</span></div>
                <div class="accordion-content">Yes! Creating and using digital QR codes for your items is completely free.</div>
            </div>
            
            <div class="accordion-item">
                <div class="accordion-header">How does it work? <span class="icon">▼</span></div>
                <div class="accordion-content">You create a tag with your contact info, download it, and attach it to your item. If someone finds it, they scan the QR and contact you.</div>
            </div>
            
            <div class="accordion-item">
                <div class="accordion-header">Is my personal data safe? <span class="icon">▼</span></div>
                <div class="accordion-content">We do not store your data permanently. Information is only used to generate your unique page linked to the QR code.</div>
            </div>

            <div class="accordion-item">
                <div class="accordion-header">What happens if I lose the downloaded file? <span class="icon">▼</span></div>
                <div class="accordion-content">Since we do not store your data permanently for security reasons, you will need to create a new QR code. It takes less than a minute!</div>
            </div>

            <div class="accordion-item">
                <div class="accordion-header">Do I need a special app to scan the code? <span class="icon">▼</span></div>
                <div class="accordion-content">No! Any modern smartphone can scan the QR code using the standard camera app.</div>
            </div>

            <div class="accordion-item">
                <div class="accordion-header">Can I edit my info after printing the QR? <span class="icon">▼</span></div>
                <div class="accordion-content">No, because the information is encoded within the code to ensure your privacy. If details change, just generate a new tag.</div>
            </div>

            <div class="accordion-item">
                <div class="accordion-header">Which format is better: PDF or PNG? <span class="icon">▼</span></div>
                <div class="accordion-content">PDF is best for high-quality home printing. PNG is better if you want to add the QR to your own design or keychain.</div>
            </div>
        </div>
        <div class="contact-section" style="text-align: center; margin-top: 20px; padding: 20px;">
            <p style="color: var(--color-dark); font-weight: 700; font-size: 18px; margin-bottom: 15px;">
                Still have questions?
            </p>
            <p style="color: #555; margin-bottom: 25px;">
                We are always ready to help you protect your things.
            </p>
            <a href="mailto:support@qrfound.com" class="email-btn" style="
                background: var(--color-primary);
                color: white;
                text-decoration: none;
                padding: 12px 30px;
                border-radius: 50px;
                font-weight: 800;
                display: inline-block;
                transition: transform 0.2s;
                box-shadow: 0 4px 15px rgba(14, 113, 86, 0.2);
            ">
                Write to us: support@qrfound.com
            </a>
        </div>
    </div>

    ''' + FOOTER_HTML + SCROLL_TOP_HTML + '''

    <script>
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            const item = header.parentElement;
            item.classList.toggle('active');
        });
    });
</script>
    ''' + SCROLL_SCRIPT + '''
</body>
</html>
''')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)