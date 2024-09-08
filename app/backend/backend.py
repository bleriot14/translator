from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from sqlmodel import Session, create_engine, select
import logging
import httpx
from orm.models import Translation, TranslationRequest

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm originlere izin ver
    allow_credentials=True,
    allow_methods=["*"],  # Tüm HTTP metodlarına izin ver
    allow_headers=["*"],  # Tüm headerlara izin ver
)
# Database setup
DATABASE_URL = "postgresql://user:password@db:5432/translations"
engine = create_engine(DATABASE_URL)

# Create tables
Translation.metadata.create_all(engine)

AIEND_URL = "http://aiend:8001/translate/"  # Adjust port as needed

@app.post("/translate/", response_model=Translation)
async def translate(request: TranslationRequest):
    logger.info(f"Received translation request: {request}")
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Sending request to AIEND service: {AIEND_URL}")
            response = await client.post(AIEND_URL, json=request.dict())
            logger.debug(f"Received response from AIEND service. Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"AIEND service error. Status: {response.status_code}, Content: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"AIEND service error: {response.text}")
            
            translation_data = response.json()
            logger.info(f"Successfully received translation data from AIEND service")
            
            # Save to database
            with Session(engine) as session:
                translation = Translation(**translation_data)
                session.add(translation)
                session.commit()
                session.refresh(translation)
                logger.info(f"Translation saved to database. ID: {translation.id}")
            
            return translation
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
            raise HTTPException(status_code=503, detail=str(exc))

@app.get("/translations/", response_model=list[Translation])
def get_translations():
    logger.info("Received request for all translations")
    with Session(engine) as session:
        translations = session.exec(select(Translation)).all()
        logger.info(f"Returning {len(translations)} translations")
        return translations

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8080)