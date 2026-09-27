import os
import uuid
import shutil
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.gemini_utils import (
    get_home_recommendations,
    get_party_recommendations,
    get_jewelry_recommendations,
)

app = FastAPI(title="PocketSmart AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(request: Request):
    return templates.TemplateResponse(request=request, name="home_planner.html", context={"result": None})


@app.post("/generate-home", response_class=HTMLResponse)
async def generate_home(
    request: Request,
    total_budget: float = Form(...),
    num_lights: int = Form(0),
    num_fans: int = Form(0),
    num_furniture: int = Form(0),
    num_dining_tables: int = Form(0),
    additional_requirements: str = Form("")
):
    result = get_home_recommendations(total_budget, num_lights, num_fans,
                                       num_furniture, num_dining_tables, additional_requirements)
    return templates.TemplateResponse(request=request, name="home_planner.html",
                                       context={"result": result})


@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(request: Request):
    return templates.TemplateResponse(request=request, name="party_planner.html", context={"result": None})


@app.post("/generate-party", response_class=HTMLResponse)
async def generate_party(
    request: Request,
    total_budget: float = Form(...),
    party_type: str = Form(...),
    num_guests: int = Form(...),
    venue_type: str = Form(""),
    needs_catering: bool = Form(False),
    needs_decoration: bool = Form(False),
    needs_entertainment: bool = Form(False),
    additional_requirements: str = Form("")
):
    result = get_party_recommendations(total_budget, party_type, num_guests, venue_type,
                                        needs_catering, needs_decoration,
                                        needs_entertainment, additional_requirements)
    return templates.TemplateResponse(request=request, name="party_planner.html",
                                       context={"result": result})


@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request):
    return templates.TemplateResponse(request=request, name="jewelry_planner.html", context={"result": None})


@app.post("/generate-jewelry", response_class=HTMLResponse)
async def generate_jewelry(
    request: Request,
    total_budget: float = Form(...),
    occasion: str = Form(...),
    preferences: str = Form(""),
    image: UploadFile = File(None)
):
    image_path = None
    if image and image.filename:
        os.makedirs("static/uploads", exist_ok=True)
        ext = os.path.splitext(image.filename)[1]
        image_path = f"static/uploads/{uuid.uuid4().hex}{ext}"
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    result = get_jewelry_recommendations(total_budget, occasion, preferences, image_path)
    return templates.TemplateResponse(request=request, name="jewelry_planner.html",
                                       context={"result": result, "uploaded_image": image_path})