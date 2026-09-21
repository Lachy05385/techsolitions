from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import Optional
import os
from pathlib import Path

# Configuración
API_BASE_URL = "http://localhost:8000"  # URL de tu API FastAPI
TOKEN_COOKIE_NAME = "auth_token"

# Aplicación
app = FastAPI(title="User Management Web Interface")

# Configuración de Jinja2
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))

# Archivos estáticos
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== UTILIDADES ==========
async def make_api_request(
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    data: Optional[dict] = None,
    files: Optional[dict] = None
):
    """Realiza una petición a la API"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                if files:
                    response = await client.post(url, data=data, files=files, headers=headers)
                else:
                    response = await client.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Método no soportado: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            print(f"Error API {e.response.status_code}: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail="Error en la API")
        except Exception as e:
            print(f"Error conexión API: {str(e)}")
            raise HTTPException(status_code=500, detail="Error de conexión con la API")

def get_token_from_request(request: Request) -> Optional[str]:
    """Obtiene el token de las cookies"""
    return request.cookies.get(TOKEN_COOKIE_NAME)

async def get_current_user(request: Request):
    """Obtiene el usuario actual desde el token"""
    token = get_token_from_request(request)
    if not token:
        return None
    
    try:
        user_data = await make_api_request("GET", "/users/profile", token=token)
        return user_data
    except:
        return None

# ========== MIDDLEWARE ==========
@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    """Añade el usuario actual a cada request"""
    request.state.user = await get_current_user(request)
    response = await call_next(request)
    return response

# ========== RUTAS PÚBLICAS ==========
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página de inicio"""
    if request.state.user:
        return RedirectResponse(url="/templates/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    if request.state.user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Procesa el login"""
    try:
        # Login en la API
        data = {"username": username, "password": password, "grant_type": "password"}
        login_data = await make_api_request("POST", "/auth/login", data=data)
        
        # Redirigir al dashboard con cookie
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key=TOKEN_COOKIE_NAME,
            value=login_data["access_token"],
            httponly=True,
            max_age=1800  # 30 minutos
        )
        return response
        
    except HTTPException as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario o contraseña incorrectos"}
        )

@app.get("/logout")
async def logout():
    """Cierra sesión"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(TOKEN_COOKIE_NAME)
    return response

# ========== RUTAS PROTEGIDAS ==========
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": request.state.user,
            "page_title": "Dashboard"
        }
    )

@app.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, page: int = 1, limit: int = 10):
    """Lista de usuarios"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    token = get_token_from_request(request)
    
    try:
        # Obtener usuarios de la API
        skip = (page - 1) * limit
        users = await make_api_request(
            "GET", 
            f"/users/?skip={skip}&limit={limit}", 
            token=token
        )
        
        # Obtener total para paginación
        all_users = await make_api_request("GET", "/users/", token=token)
        total_users = len(all_users)
        total_pages = (total_users + limit - 1) // limit
        
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "user": request.state.user,
                "page": page,
                "total_pages": total_pages,
                "page_title": "Gestión de Usuarios"
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "error": "Error al cargar usuarios",
                "user": request.state.user
            }
        )

@app.get("/users/create", response_class=HTMLResponse)
async def create_user_page(request: Request):
    """Formulario para crear usuario"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "create_user.html",
        {
            "request": request,
            "user": request.state.user,
            "page_title": "Crear Usuario"
        }
    )

@app.post("/users/create")
async def create_user_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    phone_number: str = Form(...),
    id_number: str = Form(...),
    address: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None)
):
    """Procesa la creación de usuario"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    token = get_token_from_request(request)
    
    try:
        # Preparar datos
        data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "phone_number": phone_number,
            "id_number": id_number,
            "address": address
        }
        
        files = None
        if avatar_file and avatar_file.filename:
            files = {"avatar_file": (avatar_file.filename, await avatar_file.read(), avatar_file.content_type)}
        
        # Crear usuario en la API
        await make_api_request("POST", "/users/", token=token, data=data, files=files)
        
        return RedirectResponse(url="/users", status_code=303)
        
    except HTTPException as e:
        return templates.TemplateResponse(
            "create_user.html",
            {
                "request": request,
                "user": request.state.user,
                "error": f"Error: {e.detail}",
                "form_data": {
                    "username": username,
                    "email": email,
                    "full_name": full_name,
                    "phone_number": phone_number,
                    "id_number": id_number,
                    "address": address
                }
            }
        )

@app.get("/users/{username}/edit", response_class=HTMLResponse)
async def edit_user_page(request: Request, username: str):
    """Formulario para editar usuario"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    token = get_token_from_request(request)
    
    try:
        # Obtener usuario de la API
        user_data = await make_api_request("GET", f"/users/{username}", token=token)
        
        return templates.TemplateResponse(
            "edit_user.html",
            {
                "request": request,
                "user": request.state.user,
                "edit_user": user_data,
                "page_title": f"Editar Usuario: {username}"
            }
        )
    except:
        return RedirectResponse(url="/users")

@app.post("/users/{username}/edit")
async def edit_user_submit(
    request: Request,
    username: str,
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    id_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(False)
):
    """Procesa la edición de usuario"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    token = get_token_from_request(request)
    
    try:
        # Preparar datos
        data = {}
        if full_name is not None:
            data["full_name"] = full_name
        if email is not None:
            data["email"] = email
        if phone_number is not None:
            data["phone_number"] = phone_number
        if id_number is not None:
            data["id_number"] = id_number
        if address is not None:
            data["address"] = address
        data["is_active"] = is_active
        
        # Actualizar usuario en la API
        await make_api_request("PUT", f"/users/{username}", token=token, data=data)
        
        return RedirectResponse(url="/users", status_code=303)
        
    except HTTPException as e:
        user_data = await make_api_request("GET", f"/users/{username}", token=token)
        return templates.TemplateResponse(
            "edit_user.html",
            {
                "request": request,
                "user": request.state.user,
                "edit_user": user_data,
                "error": f"Error: {e.detail}"
            }
        )

@app.get("/users/{username}/delete")
async def delete_user(request: Request, username: str):
    """Elimina un usuario"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    token = get_token_from_request(request)
    
    try:
        # Eliminar usuario de la API
        # Nota: Tu API no tiene endpoint DELETE, podrías desactivarlo
        data = {"is_active": False}
        await make_api_request("PUT", f"/users/{username}", token=token, data=data)
        
        return RedirectResponse(url="/users", status_code=303)
    except:
        return RedirectResponse(url="/users")

@app.get("/profile", response_class=HTMLResponse)
async def user_profile(request: Request):
    """Perfil del usuario actual"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": request.state.user,
            "page_title": "Mi Perfil"
        }
    )

@app.post("/profile/avatar")
async def upload_profile_avatar(
    request: Request,
    avatar_file: UploadFile = File(...)
):
    """Sube avatar para el perfil actual"""
    if not request.state.user:
        return RedirectResponse(url="/login")
    
    token = get_token_from_request(request)
    username = request.state.user["username"]
    
    try:
        files = {"file": (avatar_file.filename, await avatar_file.read(), avatar_file.content_type)}
        await make_api_request("POST", f"/users/{username}/avatar/upload", token=token, files=files)
        
        return RedirectResponse(url="/profile", status_code=303)
    except HTTPException as e:
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "user": request.state.user,
                "error": f"Error al subir avatar: {e.detail}"
            }
        )

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)