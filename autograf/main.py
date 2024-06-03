from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import sweetviz
import io
import os
import uuid

app = FastAPI(docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    content_type = file.content_type

    if content_type == "text/csv":
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    elif content_type in ["application/xml", "text/xml"]:
        df = pd.read_xml(io.BytesIO(content))
    elif content_type == "application/octet-stream":
        try:
            df = pd.read_xml(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid XML format")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Генерация отчета с помощью sweetviz
    report_id = str(uuid.uuid4())
    report_file = f"static/reports/{report_id}.html"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    report = sweetviz.analyze(df)
    report.show_html(filepath=report_file, open_browser=False)

    # Получение схемы и хоста из запроса
    host_url = str(request.url).split("/upload/")[0]

    return RedirectResponse(
        url=f"{host_url}/static/reports/{report_id}.html", status_code=303
    )


@app.get("/")
async def main():
    content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload File</title>
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-center mb-4">Быстрый доступ</h1>
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <form action="/upload/" enctype="multipart/form-data" method="post" class="border p-4 bg-light">
                        <div class="form-group">
                            <label for="file">Выберите фаил</label>
                            <input name="file" type="file" class="form-control-file" id="file">
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">Смотреть графики</button>
                    </form>
                </div>
            </div>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=content)


app.mount("/static", StaticFiles(directory="static"), name="static")
