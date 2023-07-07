from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File
from fastapi.responses import ORJSONResponse, RedirectResponse, PlainTextResponse
import schemas
import validators
from core.config import get_settings
from models import models

from sqlalchemy.orm import Session
from db.database import engine
from utils import crud, session_utils
import uvicorn
import asyncio
from sqlalchemy import update

app_settings = get_settings()
get_session = session_utils.get_session

app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=app_settings.app_title,  # название приложение берём из настроек
    # Адрес документации в красивом интерфейсе
    docs_url='/api/openapi',
    # Адрес документации в формате OpenAPI
    openapi_url='/api/openapi.json',
    # Можно сразу сделать небольшую оптимизацию сервиса
    # и заменить стандартный JSON-сериализатор на более шуструю версию, написанную на Rust
    default_response_class=ORJSONResponse)


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

    await engine.dispose()


async def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


async def raise_not_found(request):
    message = f"URL '{request.url}' не существует"
    raise HTTPException(status_code=404, detail=message)


async def raise_gone():
    message = f"Целевой ресурс больше недоступен на сервере происхождения"
    raise HTTPException(status_code=410, detail=message)


@app.get("/")
async def read_root():
    return "Добро пожаловать в сервис по созданию сокращенной формы передаваемых url"


@app.get('/get_status_db')
async def get_status_db(db: Session = Depends(get_session)):
    try:
        results = await db.execute("""SELECT pg_database_size('collection') database_size""")
        res = 'Подключение к БД выполнено успешно'
    except Exception as e:
        res = f'Возникли проблемы с подключением к БД {e}'
    return res


@app.post("/url", response_model=schemas.URLInfo)
async def create_url(url: schemas.URLBase, db: Session = Depends(get_session)):
    if not validators.url(url.target_url):
        await raise_bad_request(message="Твой url является невалидным")

    db_url = await crud.create_db_url(db=db, url=url)
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key

    return db_url


@app.delete("/delete/{url_key}")
async def delete_url(url_key: str, db: Session = Depends(get_session)):
    stmt = (
        update(models.URL).
        where(models.URL.key == url_key).
        values(is_delete=True)
    )

    await db.execute(statement=stmt)
    await db.commit()

    return 'Удаление URL c ключом  выполнено успешно'


@app.get("/{url_key}")
async def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_session)
):
    if db_url := await crud.get_db_url_by_key(db=db, url_key=url_key):
        if not db_url[0].is_delete:
            await crud.update_db_clicks(db=db, db_url=db_url)
            return RedirectResponse(db_url[0].target_url)
        else:
            await raise_gone()
    else:
        await raise_not_found(request)


@app.post("/file/upload-file")
async def butch_upload_file(file: UploadFile, db: Session = Depends(get_session)):
    urls = []
    for line in file.file:
        url = schemas.URLBase(target_url=line.decode('utf-8').rstrip())
        db_url = await create_url(url=url, db=db)
        res = {
            'url': db_url.target_url,
            'key': db_url.key
        }
        urls.append(res)
    return urls


if __name__ == '__main__':
    # Приложение может запускаться командой
    # `uvicorn main:app --host 0.0.0.0 --port 8080`
    # но чтобы не терять возможность использовать дебагер,
    # запустим uvicorn сервер через python
    asyncio.run(main())
    uvicorn.run(
        'main:app'
    )
