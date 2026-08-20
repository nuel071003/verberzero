import os
import torch
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from transformers import AutoModelForSequenceClassification, AutoTokenizer

app = Flask(__name__)

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CLICKBAIT_PATH = os.path.join(BASE_DIR, "models", "model_clickbait")
MODEL_HOAX_PATH = os.path.join(BASE_DIR, "models", "model_hoax")

# Load Tokenizers and Models
print("Loading Clickbait Model...")
tokenizer_cb = AutoTokenizer.from_pretrained(MODEL_CLICKBAIT_PATH)
model_cb = AutoModelForSequenceClassification.from_pretrained(MODEL_CLICKBAIT_PATH, num_labels=2)

print("Loading Hoax Model...")
tokenizer_hx = AutoTokenizer.from_pretrained(MODEL_HOAX_PATH)
model_hx = AutoModelForSequenceClassification.from_pretrained(MODEL_HOAX_PATH, num_labels=2)

def scrape_article(url):
    try:
        import re
        # Menambahkan User-Agent agar tidak diblokir oleh beberapa website berita
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ekstraksi Judul
        title = ""
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        elif soup.title:
            title = soup.title.get_text(strip=True)
            
        # Buang elemen yang bukan bagian dari artikel (header, footer, nav, iklan, dsb)
        for tag in soup(["header", "footer", "nav", "aside", "script", "style", "noscript", "form", "button"]):
            tag.decompose()
            
        # Hapus berdasarkan class atau id yang tidak relevan
        ignore_patterns = re.compile(r"header|footer|sidebar|menu|nav|widget|comment|promo|advert|social|share|tags|author-info", re.I)
        for tag in soup.find_all(attrs={"class": ignore_patterns}):
            tag.decompose()
        for tag in soup.find_all(attrs={"id": ignore_patterns}):
            tag.decompose()

        # Prioritaskan kontainer artikel jika ada
        article_container = soup.find('article') or soup.find('main') or soup
            
        # Ekstraksi Paragraf (Isi Berita)
        paragraphs = article_container.find_all('p')
        valid_paragraphs = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            # Ambil paragraf yang cukup panjang (mengabaikan teks pendek seperti "Baca juga:" atau copyright)
            if len(text) > 30:
                valid_paragraphs.append(text)
                
        content = " ".join(valid_paragraphs)
        
        # Pembersihan teks iklan in-article spesifik
        content = re.sub(r'(?i)SCROLL TO CONTINUE WITH CONTENT', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        return title, content
    except Exception as e:
        print(f"Scraping error: {e}")
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    url = request.form.get('url')
    if not url:
        return render_template('index.html', error="URL tidak boleh kosong.")
        
    title, content = scrape_article(url)
    
    if not title or not content:
        return render_template('index.html', error="Gagal mengambil konten dari URL. Pastikan URL valid dan dapat diakses.")
        
    # --- Prediksi Clickbait (Berdasarkan Judul) ---
    inputs_cb = tokenizer_cb(title, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs_cb = model_cb(**inputs_cb)
        probs_cb = torch.nn.functional.softmax(outputs_cb.logits, dim=-1)
        pred_cb = torch.argmax(probs_cb, dim=-1).item()
        conf_cb = probs_cb[0][pred_cb].item() * 100
        
    # Mapping label: 0 = non-clickbait, 1 = clickbait
    cb_status = "Clickbait" if pred_cb == 1 else "Non-Clickbait"
    
    if pred_cb == 1:
        import re
        parts = re.split(r'([,?!|:-])', title, 1)
        if len(parts) > 1:
            title_analyzed = f'<span class="bg-warning text-dark px-1 rounded fw-bold">{parts[0]}</span>' + "".join(parts[1:])
        else:
            words = title.split()
            half = max(1, int(len(words) * 0.7))
            title_analyzed = f'<span class="bg-warning text-dark px-1 rounded fw-bold">{" ".join(words[:half])}</span> ' + " ".join(words[half:])
    else:
        title_analyzed = title
    
    # --- Prediksi Hoaks (Berdasarkan Isi Berita) ---
    inputs_hx = tokenizer_hx(content, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs_hx = model_hx(**inputs_hx)
        probs_hx = torch.nn.functional.softmax(outputs_hx.logits, dim=-1)
        pred_hx = torch.argmax(probs_hx, dim=-1).item()
        conf_hx = probs_hx[0][pred_hx].item() * 100

    # Mapping label: 0 = Non-Hoax, 1 = Hoax
    hx_status = "Hoax" if pred_hx == 1 else "Non Hoax"
    
    if pred_hx == 1:
        import re
        # Pecah teks menjadi kalimat-kalimat
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if len(s.strip()) > 10]
        
        if not sentences:
            snippet = content[:200] + "..."
        else:
            best_sentence = sentences[0]
            max_prob = -1
            best_idx = 0
            
            # Evaluasi maksimal 15 kalimat pertama
            for i, s in enumerate(sentences[:15]):
                inp = tokenizer_hx(s, return_tensors="pt", truncation=True, max_length=128)
                with torch.no_grad():
                    out = model_hx(**inp)
                    prob = torch.nn.functional.softmax(out.logits, dim=-1)[0][1].item()
                    
                    if prob > max_prob:
                        max_prob = prob
                        best_sentence = s
                        best_idx = i
            
            # Ambil 2 kalimat
            start_idx = max(0, best_idx - 1)
            end_idx = min(len(sentences), start_idx + 2)
            if best_idx >= end_idx:
                start_idx = best_idx
                end_idx = min(len(sentences), start_idx + 2)
                
            context_sentences = sentences[start_idx:end_idx]
            
            highlighted = []
            for s in context_sentences:
                if s == best_sentence:
                    highlighted.append(f'<span class="bg-warning text-dark px-1 rounded fw-bold">{s}</span>')
                else:
                    highlighted.append(s)
            
            snippet = " ".join(highlighted)
    else:
        snippet = content[:300] + "..." if len(content) > 300 else content
    
    # Format data untuk dikirim ke template hasil.html
    hasil = {
        "is_placeholder": False,
        "judul": title,
        "url": url,
        "isi_teks": content,
        "isi_preview": snippet,
        "clickbait": {
            "status": cb_status,
            "judul_analyzed": title_analyzed,
            "confidence": f"{conf_cb:.1f}"
        },
        "hoax": {
            "status": hx_status,
            "isi_analyzed": snippet,
            "confidence": f"{conf_hx:.1f}"
        }
    }
    
    return render_template('hasil.html', hasil=hasil)

if __name__ == '__main__':
    app.run(debug=False)
