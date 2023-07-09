from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from core.config import get_settings
from models import models

from db.database import engine
import uvicorn

from api.v2 import base

app_settings = get_settings()


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

app.include_router(base.router, prefix='/api/v2')


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

    await engine.dispose()


if __name__ == '__main__':
    uvicorn.run(
        'main:app'
    )
