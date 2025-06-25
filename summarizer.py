import fitz  # PDF reading (PyMuPDF)
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

# Load summarizer components
tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6")
model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6")
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=-1)

# Extract text from all pages in a PDF.
def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# Summarize first part of the text.
def summarize_text(text, max_chars=2000):
    snippet = text[:max_chars]
    result = summarizer(snippet, max_length=130, min_length=50, do_sample=False)[0]["summary_text"]
    return result