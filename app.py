from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import functools, re, zeyrek

app = FastAPI(title="TR Lemmatizer (zeyrek)")

@functools.lru_cache(maxsize=1)
def get_analyzer():
    return zeyrek.MorphAnalyzer()

_ws = re.compile(r"\s+", re.U)

class LemReq(BaseModel):
    tokens: Optional[List[str]] = None
    text: Optional[str] = None
    return_details: bool = False

def _tokenize(text: str) -> List[str]:
    return [t for t in _ws.split(text.strip()) if t]

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/lemmatize")
def lemmatize(req: LemReq) -> Dict[str, Any]:
    tokens = req.tokens or ( _tokenize(req.text or "") if req.text else [] )
    analyzer = get_analyzer()
    lemmas, details = [], []
    for tok in tokens:
        result = analyzer.lemmatize(tok)
        lemma = (result[0][0] if result else tok)
        lemmas.append(lemma)
        if req.return_details:
            analyses = analyzer.analyze(tok)
            details.append({"token": tok, "lemma": lemma, "analyses": [str(a) for a in analyses]})
    out = {"lemmas": lemmas}
    if req.return_details: out["details"] = details
    return out
