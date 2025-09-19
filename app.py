from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import functools, re, logging, os
import zeyrek
import nltk

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("zeyrek-svc")

app = FastAPI(title="TR Lemmatizer (zeyrek)")

CACHE_DIR = os.environ.get("ZEYREK_CACHE_DIR", "/srv/.zeyrek_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Set NLTK data path
NLTK_DATA_DIR = os.environ.get("NLTK_DATA", "/usr/local/share/nltk_data")
os.environ["NLTK_DATA"] = NLTK_DATA_DIR


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
        log.info("Ensuring NLTK data is available...")
        
        # Check and download punkt data
        try:
            nltk.data.find('tokenizers/punkt')
            log.info("NLTK punkt data found.")
        except (LookupError, OSError) as e:
            log.info("NLTK punkt data not found, downloading...")
            nltk.download('punkt', quiet=True)
            log.info("NLTK punkt data downloaded.")
        
        # Check and download punkt_tab data
        try:
            nltk.data.find('tokenizers/punkt_tab')
            log.info("NLTK punkt_tab data found.")
        except (LookupError, OSError) as e:
            log.info("NLTK punkt_tab data not found, downloading...")
            nltk.download('punkt_tab', quiet=True)
            log.info("NLTK punkt_tab data downloaded.")
        
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
            # Zeyrek lemmatize returns [('token', ['lemma1', 'lemma2', ...])]
            # We want the first lemma from the list: result[0][1][0]
            if result and len(result) > 0 and len(result[0]) > 1 and result[0][1]:
                # Get all lemmas
                lemmas_list = result[0][1]
                # Get analyses to determine POS tags
                analyses = a.analyze(tok)
                
                # Prefer nouns over verbs, then common nouns over proper nouns
                noun_lemmas = []
                verb_lemmas = []
                other_lemmas = []
                
                # analyses is a list, and analyses[0] is also a list of Parse objects
                if analyses and len(analyses) > 0:
                    for analysis in analyses[0]:
                        if hasattr(analysis, 'pos') and analysis.pos == 'Noun':
                            noun_lemmas.append(analysis.lemma)
                        elif hasattr(analysis, 'pos') and analysis.pos == 'Verb':
                            verb_lemmas.append(analysis.lemma)
                        else:
                            other_lemmas.append(analysis.lemma)
                
                # Choose the best lemma: nouns > verbs > others
                if noun_lemmas:
                    lemma = noun_lemmas[0]
                elif verb_lemmas:
                    lemma = verb_lemmas[0]
                elif other_lemmas:
                    lemma = other_lemmas[0]
                else:
                    lemma = lemmas_list[0]  # Fallback to first lemma
            else:
                lemma = tok
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
