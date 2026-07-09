from fastapi import FastAPI

app = FastAPI(
    title="Inventory API",
    description="Inventory and order management backend with stock validation, order workflows, and reporting.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}