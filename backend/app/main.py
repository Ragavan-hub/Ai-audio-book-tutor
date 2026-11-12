import uuid,json
from pathlib import Path
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from .config import settings
from . import core
app=FastAPI(title="AI Audio Book Tutor API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-audio-book-tutor.vercel.app",
        "http://localhost:3000",
        settings.frontend_origin.rstrip("/")
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def startup():core.init()
@app.get("/")
def root():return {"message":"AI Audio Book Tutor API running"}
@app.get("/health")
def health():return {"status":"ok","provider":settings.ai_provider}
@app.post("/api/books/upload")
async def upload(file:UploadFile=File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):raise HTTPException(400,"Upload a PDF.")
    raw=await file.read()
    if len(raw)>settings.max_upload_mb*1024*1024:raise HTTPException(413,"PDF too large.")
    bid=Path(file.filename).stem.replace(" ","-")[:45]+"-"+uuid.uuid4().hex[:8]
    pdf=core.BOOKS/f"{bid}.pdf";pdf.write_bytes(raw)
    try:pages,chunks=core.extract_pdf(pdf)
    except ValueError as e:pdf.unlink(missing_ok=True);raise HTTPException(422,str(e))
    data={"book_id":bid,"filename":file.filename,"pages":pages,"chunks":chunks}
    core.book_path(bid).write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    return {"book_id":bid,"filename":file.filename,"page_count":len(pages)}
@app.get("/api/books/{bid}/page/{number}")
def page(bid:str,number:int):
    try:
        b=core.get_book(bid);p=next((x for x in b["pages"] if x["page"]==number),None)
        if not p:raise HTTPException(404,"Page not found")
        return p
    except FileNotFoundError as e:raise HTTPException(404,str(e))
class Ask(BaseModel):
    book_id:str;question:str=Field(min_length=2,max_length=3000);provider:str|None=None
class Explain(BaseModel):
    book_id:str;page:int=Field(ge=1);style:str="simple";provider:str|None=None
@app.post("/api/ai/ask")
def ask(x:Ask):
    try:
        b=core.get_book(x.book_id);hits=core.retrieve(b,x.question)
        if not hits:return {"answer":"No relevant passage found in this book.","sources":[]}
        ctx="\\n\\n".join(f"[Page {h['page']}] {h['text']}" for h in hits)
        prompt=f"Answer only from this book context. If unsupported say so. Cite page numbers.\\n{ctx}\\nQuestion: {x.question}"
        return {"answer":core.ai(prompt,x.provider),"sources":sorted(set(h["page"] for h in hits))}
    except Exception as e:raise HTTPException(502,str(e))
@app.post("/api/ai/explain")
def explain(x:Explain):
    try:
        b=core.get_book(x.book_id);p=next((v for v in b["pages"] if v["page"]==x.page),None)
        if not p:raise HTTPException(404,"Page not found")
        style={"simple":"Explain simply for a beginner with an example.","moderate":"Explain key concepts with examples.","detailed":"Give a detailed teaching explanation and recap."}.get(x.style,"Explain simply.")
        return {"explanation":core.ai(f"You are an AI Book Tutor. {style} Use only source text.\\n{p['text']}",x.provider)}
    except Exception as e:raise HTTPException(502,str(e))
class Speak(BaseModel):
    text:str=Field(min_length=1,max_length=12000)
@app.post("/api/audio/speak")
async def speak(x:Speak):
    try:
        import edge_tts
        name=uuid.uuid4().hex+".mp3";path=core.AUDIO/name
        await edge_tts.Communicate(x.text,"en-US-AriaNeural").save(str(path))
        return {"audio_url":"/api/audio/file/"+name}
    except Exception as e:raise HTTPException(502,str(e))
@app.get("/api/audio/file/{name}")
def audio(name:str):
    if Path(name).name!=name or not name.endswith(".mp3"):raise HTTPException(400,"Invalid filename")
    p=core.AUDIO/name
    if not p.exists():raise HTTPException(404,"Audio not found")
    return FileResponse(p,media_type="audio/mpeg")
class Progress(BaseModel):
    book_id:str;page:int=Field(ge=1);completed:bool=False
@app.get("/api/progress/{bid}")
def get_progress(bid:str):return core.progress_read().get(bid,{"last_page":1,"completed_pages":[]})
@app.post("/api/progress")
def save_progress(x:Progress):
    d=core.progress_read();v=d.get(x.book_id,{"last_page":1,"completed_pages":[]});v["last_page"]=x.page
    if x.completed and x.page not in v["completed_pages"]:v["completed_pages"].append(x.page)
    d[x.book_id]=v;core.PROGRESS.write_text(json.dumps(d,indent=2));return v
