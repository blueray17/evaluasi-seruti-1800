# evaluasi-seruti-1800

requirement :
  - fastapi
  - uvicorn
  - httpx
  - jinja2
  - toml // kalo query disimpan dlm format toml
  - dotenv // kl setting disimpan di .env
  - pandas <---- pake python3-pandas
  - python3-multipart <---- untuk form

Cara penggunaan :
  1. git clone, masuk folder evaluasi-seruti-1800
  2. masuk virtual environtment : source seruti/bin/activate
  3. install requirement
  4. instal pandas
  5. jalankan : uvicorn main:app --reload
