from sentence_transformers import SentenceTransformer

# Specify the model name
model_name = "all-MiniLM-L6-v2"

# Download and cache the model
model = SentenceTransformer(model_name)
print(f"Downloaded and cached model {model_name}")
