# TR Lemmatizer (zeyrek)

FastAPI tabanlı Türkçe lemmatization servisi.

## Çalıştırma

```bash
docker compose up -d --build
curl -s http://localhost:8077/health
curl -s -X POST http://localhost:8077/lemmatize \
  -H 'Content-Type: application/json' \
  -d '{"tokens":["kademe","ilerlemesi"],"return_details":true}'
````

Yanıt örneği:

```json
{
  "lemmas": ["kademe", "ilerleme"],
  "details": [
    {"token":"kademe","lemma":"kademe","analyses":["..."]},
    {"token":"ilerlemesi","lemma":"ilerleme","analyses":["..."]}
  ]
}
```

## Ortam Değişkenleri

* Yok (gerekirse ileride eklenebilir)

## Notlar

* CPU/RAM limitleri docker-compose içinde ayarlı.
