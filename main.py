import os
import zipfile
import io
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, send_file, url_for, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Flash mesajları için gerekli

# Kullanıcı adlarını çıkartmak için bir fonksiyon
def kullanici_adlarini_cek(zip_dosyasi, dosya_adi):
    kullanicilar = []
    
    with zipfile.ZipFile(zip_dosyasi, 'r') as zip_ref:
        dosyalar = [f for f in zip_ref.namelist() if dosya_adi in f and f.endswith(".html")]
        
        if not dosyalar:
            return kullanicilar
        
        for filename in dosyalar:
            with zip_ref.open(filename) as file:
                content = file.read().decode('utf-8')
                soup = BeautifulSoup(content, "html.parser")

                kullanicilar.extend(
                    a_tag.text.strip() for a_tag in soup.find_all("a", href=True) 
                    if "instagram.com" in a_tag['href'] and a_tag.text.strip()
                )
    
    return kullanicilar

# Kullanıcı adlarını çıkartma işlemi
def extract_usernames(zip_dosyasi):
    follower_prefix = 'connections/followers_and_following/followers_'
    following_prefix = 'connections/followers_and_following/following.html'
    
    takipciler = kullanici_adlarini_cek(zip_dosyasi, follower_prefix)
    takip_edilenler = kullanici_adlarini_cek(zip_dosyasi, following_prefix)
    
    takip_etmiyor = set(takip_edilenler) - set(takipciler)

    # HTML formatında sonuçları oluştur
    output = io.BytesIO()
    html_content = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Takip Etmeyen Kullanıcılar</title>
    <style>
        body {
            background-color: #1a1a1a;  /* Koyu arka plan rengi */
            color: #ffffff;  /* Açık metin rengi */
            font-family: 'Arial', sans-serif;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);  /* Başlık için gölge */
        }
        ul {
            list-style-type: none;  /* Madde işaretlerini kaldır */
            padding: 0;
        }
        li {
            margin: 15px 0;  /* Liste elemanları arası boşluk */
            padding: 10px;
            border: 1px solid #444;  /* Kenar rengi */
            border-radius: 5px;  /* Kenar yuvarlama */
            transition: background-color 0.3s;  /* Geçiş efekti */
        }
        li:hover {
            background-color: #333;  /* Hover durumunda arka plan rengi */
        }
        a {
            color: #fff;  /* Link rengi */
            text-decoration: none;
            font-size: 25px;  /* Font boyutu */
        }
        a:hover {
            text-decoration: none;  /* Hover efekt */
            color: orange;  /* Hover durumu için renk değişimi */
        }
        .container {
            max-width: 800px;  /* Maksimum genişlik */
            margin: 0 auto;  /* Ortalanmış görünüm */
            padding: 20px;
            background-color: #222;  /* İçerik alanının arka plan rengi */
            border-radius: 10px;  /* Köşeleri yuvarlaştır */
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Takip Etmeyen Kullanıcılar</h1>
        <ul>
"""

    for username in takip_etmiyor:
        html_content += f'<li><a href="https://instagram.com/{username}" target="_blank">{username}</a></li>'

    html_content += """
        </ul>
    </div>
</body>
</html>
"""
    output.write(html_content.encode('utf-8'))
    output.seek(0)  # Dosyanın başına geri dön
    
    return output

# Ana sayfa ve dosya yükleme
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Lütfen bir dosya seçin.', 'danger')
            return redirect(request.url)

        zip_file = request.files['file']

        if zip_file.filename == '':
            flash('Dosya seçilmedi.', 'danger')
            return redirect(request.url)
        
        if zip_file and zip_file.filename.endswith('.zip'):
            # Bellekte dosya işle
            extracted_data = extract_usernames(zip_file)

            # takip_etmiyor.html dosyasını indirme linkine yönlendir
            return send_file(extracted_data, mimetype="text/html", as_attachment=True, download_name="takip_etmiyor.html")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
