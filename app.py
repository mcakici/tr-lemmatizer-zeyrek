from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import functools, re, logging, os
import zeyrek

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("zeyrek-svc")

app = FastAPI(title="TR Lemmatizer (zeyrek)")

CACHE_DIR = os.environ.get("ZEYREK_CACHE_DIR", "/srv/.zeyrek_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


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


@app.on_event("startup")
async def warmup():
    try:
        log.info("Warming up Zeyrek (cache: %s)...", CACHE_DIR)
        a = get_analyzer()
        a.lemmatize("deneme")
        log.info("Warmup OK.")
    except Exception as e:
        log.exception("Warmup failed: %s", e)
        raise


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/lemmatize")
def lemmatize(req: LemReq) -> Dict[str, Any]:
    try:
        if not (req.tokens or req.text):
            return {"lemmas": [], "details": []}

        tokens = req.tokens or _tokenize(req.text or "")
        a = get_analyzer()

        lemmas: List[str] = []
        details: List[Dict[str, Any]] = []

        for tok in tokens:
            result = a.lemmatize(tok)
            lemma = result[0][0] if result else tok
            lemmas.append(lemma)
            if req.return_details:
                analyses = a.analyze(tok)
                details.append(
                    {
                        "token": tok,
                        "lemma": lemma,
                        "analyses": [str(x) for x in analyses],
                    }
                )

        out = {"lemmas": lemmas}
        if req.return_details:
            out["details"] = details
        return out
    except Exception as e:
        log.exception("lemmatize failed: %s", e)
        raise HTTPException(status_code=500, detail=f"lemmatize_failed: {e}")
