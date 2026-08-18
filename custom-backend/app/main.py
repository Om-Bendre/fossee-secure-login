from fastapi import FastAPI

app = FastAPI(title="FOSSEE Secure Login")

@app.get("/")
def root():
    return {"message": "FOSSEE Secure Login API"}