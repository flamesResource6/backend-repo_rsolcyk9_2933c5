import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# --------------------------------------------------
# Video API
# --------------------------------------------------
class VideoIn(BaseModel):
    title: str
    description: Optional[str] = ""
    thumbnail_url: str
    video_url: str
    channel_name: str = "Unknown Creator"
    tags: List[str] = []

@app.post("/api/videos")
def add_video(video: VideoIn):
    from schemas import Video as VideoSchema
    vid = VideoSchema(**video.model_dump())
    inserted_id = create_document("video", vid)
    return {"id": inserted_id}

@app.get("/api/videos")
def list_videos():
    videos = get_documents("video", {}, limit=50)
    # map _id to id and stringify
    for v in videos:
        v["id"] = str(v.get("_id"))
        v.pop("_id", None)
    return {"items": videos}

@app.get("/api/videos/{video_id}")
def get_video(video_id: str):
    try:
        doc = db["video"].find_one({"_id": ObjectId(video_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Video not found")
        doc["id"] = str(doc["_id"]) 
        doc.pop("_id", None)
        return doc
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
