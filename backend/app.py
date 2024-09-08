from fastapi import FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from transformers import SeamlessM4Tv2ForTextToText, SeamlessM4TTokenizer, SeamlessM4TFeatureExtractor
import torch
import time
from typing import Optional
import logging
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define SQLModel for Translation
class Translation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    total_time: float
    input_prep_time: float
    translation_time: float
    decoding_time: float
    model_load_time: float = Field(default=0.0)  # Add this line

# Define request model
class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

# Create FastAPI app
app = FastAPI()

# Database setup
DATABASE_URL = "sqlite:///./translation_database.db"
engine = create_engine(DATABASE_URL)

# Create tables
SQLModel.metadata.create_all(engine)

# Load model and tokenizer
MODEL_PATH = "models/seamless-m4t-v2-large"
logger.info(f"Loading model from {MODEL_PATH}")

try:
    model = SeamlessM4Tv2ForTextToText.from_pretrained(MODEL_PATH)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    raise

try:
    tokenizer = SeamlessM4TTokenizer.from_pretrained(MODEL_PATH)
    feature_extractor = SeamlessM4TFeatureExtractor.from_pretrained(MODEL_PATH)
    logger.info("Tokenizer and Feature Extractor loaded successfully")
except Exception as e:
    logger.error(f"Error loading tokenizer or feature extractor: {str(e)}")
    raise

device = torch.device("cpu")
model = model.to(device)

@app.post("/translate/", response_model=Translation)
def translate(request: TranslationRequest):
    start_time = time.time()

    # Prepare the input
    input_prep_start = time.time()
    inputs = tokenizer(request.text, return_tensors="pt", src_lang=request.source_lang)
    input_prep_time = time.time() - input_prep_start

    # Generate translation
    translation_start = time.time()
    with torch.no_grad():
        output_tokens = model.generate(**inputs, tgt_lang=request.target_lang)
    translation_time = time.time() - translation_start

    # Decode the output
    decoding_start = time.time()
    translated_text = tokenizer.decode(output_tokens[0].tolist(), skip_special_tokens=True)
    decoding_time = time.time() - decoding_start

    total_time = time.time() - start_time

    # Create Translation object
    translation = Translation(
        original_text=request.text,
        translated_text=translated_text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        total_time=total_time,
        input_prep_time=input_prep_time,
        translation_time=translation_time,
        decoding_time=decoding_time,
        model_load_time=0.0  # Add this line, or calculate the actual model load time if available
    )

    # Save to database
    with Session(engine) as session:
        session.add(translation)
        session.commit()
        session.refresh(translation)

    return translation

@app.get("/translations/", response_model=list[Translation])
def get_translations():
    with Session(engine) as session:
        translations = session.exec(select(Translation)).all()
        return translations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)