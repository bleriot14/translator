from fastapi import FastAPI
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from transformers import SeamlessM4Tv2ForTextToText, SeamlessM4TTokenizer, SeamlessM4TFeatureExtractor
import torch
import time
import logging
from orm.models import TranslationRequest, Translation
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
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

# Load model and tokenizer
MODEL_PATH = "models/seamless-m4t-v2-large"
logger.info(f"Loading model from {MODEL_PATH}")

try:
    model = SeamlessM4Tv2ForTextToText.from_pretrained(MODEL_PATH)
    tokenizer = SeamlessM4TTokenizer.from_pretrained(MODEL_PATH)
    feature_extractor = SeamlessM4TFeatureExtractor.from_pretrained(MODEL_PATH)
    logger.info("Model, Tokenizer, and Feature Extractor loaded successfully")
except Exception as e:
    logger.error(f"Error loading model components: {str(e)}")
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
        model_load_time=0.0
    )

    return translation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)