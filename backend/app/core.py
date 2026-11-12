import json,re,uuid
from pathlib import Path
import fitz,httpx
from google import genai
from google.genai import types
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .config import settings
DATA=Path(settings.data_dir); BOOKS=DATA/"books"; AUDIO=DATA/"audio"; PROGRESS=DATA/"progress.json"
def init():
    BOOKS.mkdir(parents=True,exist_ok=True); AUDIO.mkdir(parents=True,exist_ok=True)
def book_path(bid): return BOOKS/f"{bid}.json"
def get_book(bid):
    p=book_path(bid)
    if not p.exists(): raise FileNotFoundError("Book not found. Upload the PDF again.")
    return json.loads(p.read_text(encoding="utf-8"))
def extract_pdf(path):
    doc=fitz.open(path); pages=[]
    for i,p in enumerate(doc):
        t=p.get_text("text").strip()
        if t: pages.append({"page":i+1,"text":t})
    doc.close()
    if not pages: raise ValueError("No selectable text found; scanned PDFs are not supported.")
    chunks=[]
    for p in pages:
        txt=re.sub(r"\\s+"," ",p["text"])
        for i in range(0,len(txt),1200): chunks.append({"page":p["page"],"text":txt[i:i+1200]})
    return pages,chunks
def ai(prompt,provider=None):
    mode=(provider or settings.ai_provider).lower()
    if mode=="ollama":
        r=httpx.post(settings.ollama_base_url.rstrip("/")+"/api/generate",json={"model":settings.ollama_model,"prompt":prompt,"stream":False},timeout=180)
        r.raise_for_status(); return r.json().get("response","")
    if not settings.gemini_api_key: raise RuntimeError("Set GEMINI_API_KEY in backend environment.")
    client=genai.Client(api_key=settings.gemini_api_key)
    out=client.models.generate_content(model=settings.gemini_model,contents=prompt,config=types.GenerateContentConfig(temperature=.4,max_output_tokens=1800))
    return out.text or ""
def retrieve(book,q):
    docs=book["chunks"]
    if not docs:return []
    try:
        m=TfidfVectorizer(stop_words="english").fit_transform([x["text"] for x in docs]+[q])
        s=cosine_similarity(m[-1],m[:-1]).ravel()
        return [docs[i] for i in s.argsort()[::-1][:5] if s[i]>0]
    except ValueError:return docs[:3]
def progress_read():
    try:return json.loads(PROGRESS.read_text(encoding="utf-8"))
    except:return {}
