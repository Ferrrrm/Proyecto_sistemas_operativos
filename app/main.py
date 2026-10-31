import os
import redis
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import database, models

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

app = FastAPI(title="CRUD Cloud App", version="1.0.0")
models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido a la web en la nube con FastAPI, Postgres y Redis!"}

@app.get("/health")
def health_check():
    # Verificamos estado de Redis y Postgres
    redis_status = "connected"
    try:
        redis_client.ping()
    except Exception:
        redis_status = "disconnected"
        
    return {"status": "healthy", "redis": redis_status}

@app.get("/visits")
def record_visit():
    visits = redis_client.incr("visitor_count")
    return {"message": "Visita registrada en caché de Redis", "total_visits": visits}

@app.post("/articles/")
def create_article(title: str, content: str, owner_id: int, db: Session = Depends(database.get_db)):
    db_article = models.Article(title=title, content=content, owner_id=owner_id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@app.get("/articles/")
def get_articles(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    articles = db.query(models.Article).offset(skip).limit(limit).all()
    return articles

@app.delete("/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(database.get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    db.delete(db_article)
    db.commit()
    return {"message": "Artículo eliminado correctamente"}