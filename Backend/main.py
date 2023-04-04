import jwt
from fastapi import FastAPI, HTTPException,Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from datetime import datetime, timedelta


app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBasic()


mydb = mysql.connector.connect(
    # user=admin_bd
    # password=admin123
    host="db4free.net",
    port="3306",
    user="admin_bd",
    password="admin123",
    database="notas_bd"
)
mycursor = mydb.cursor()

mycursor.execute("SELECT * FROM usuarios")

result = mycursor.fetchall()


class User(BaseModel):
    username: str
    password: str

class Note(BaseModel):
    id:int
    titulo: str
    texto: str
    hora: str
    fecha: str
    likes: int
    color: str
    usuario_id: int
    imagen: Optional[str] = None




# Definir una clave secreta para cifrar el token
SECRET_KEY = "my-secret-key"

# Definir la duración del token (en minutos)
TOKEN_EXPIRATION = 30

@app.post("/users/")
async def create_user(user: User):
    query = "INSERT INTO usuarios (users, password) VALUES (%s, %s)"
    values = (user.username, user.password)
    mycursor.execute(query, values)
    mydb.commit()
    return {"message": "Usuario creado exitosamente"}


@app.post("/login")
async def login(credentials: HTTPBasicCredentials):
    query = "SELECT id FROM usuarios WHERE users=%s AND password=%s"
    values = (credentials.username, credentials.password)
    mycursor.execute(query, values)
    user = mycursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Generar el token utilizando el módulo jwt
    token_data = {
        "sub": user[0],
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    # Devolver el token en la respuesta
    response = JSONResponse(content={"id": user[0], "token": token})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def get_log_user(credentials: HTTPBasicCredentials = Depends(security)):
    query = "SELECT id FROM usuarios WHERE users=%s AND password=%s"
    values = (credentials.username, credentials.password)
    mycursor.execute(query, values)
    user = mycursor.fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return user[0]

# Función para obtener las notas de un usuario a partir de su id
@app.get("/notas/{usuario_id}")
async def get_notas_usuario(usuario_id: int, user=get_log_user):
    query = "SELECT * FROM notas WHERE usuario_id = %s"
    values = (usuario_id,)
    mycursor.execute(query, values)
    response = mycursor.fetchall()
    return response



@app.get("/all")
async def get_notes():
    query = "SELECT * FROM notas "
    mycursor.execute(query)
    response=mycursor.fetchall()
    return response

@app.post("/notas")
async def create_note(note: Note):
    query = "INSERT INTO notas (titulo, texto, hora, fecha, likes, color, usuario_id, imagen) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)"
    values = (note.titulo, note.texto, note.hora, note.fecha, note.likes, note.color, note.usuario_id, note.imagen)
    mycursor.execute(query, values)
    mydb.commit()
    return {"message": "Nota creada exitosamente"}





if __name__ == "__main__":
    uvicorn.run(app)
