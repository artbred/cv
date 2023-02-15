import asyncio
from typing import Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from labels import calculate_embedding, get_label_by_id, get_most_similar_label
from pydantic import BaseModel, validator
from settings import known_utm_tags, min_similarity_score
from storage import save_download_by_label_id, save_query_position, save_utm_params
from tokens import decrypt_label_id, encrypt_label_id

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    position: str

    @validator("position")
    def check_position(cls, value):
        if len(value) < 5 or len(value) > 50:
            raise ValueError("Position must be between 5 and 50 characters long")
        return value


class DownloadRequest(BaseModel):
    token: str


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    combined_errors_msg = ", ".join(str(error.get("msg")) for error in exc.errors())
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"info": exc.errors(), "body": exc.body, "detail": combined_errors_msg}),
    )


@app.middleware("http")
async def utm_params_middleware(request: Request, call_next):
    endpoint = request.url.path.replace("/", "")
    query_params = request.query_params
    utm_params = {}

    for key in query_params:
        if key in known_utm_tags and len(query_params[key]) < 50:
            utm_params[key] = query_params[key]

    if len(utm_params) > 0:
        request.state.utm_params = utm_params
        asyncio.create_task(save_utm_params(endpoint, utm_params))

    return await call_next(request)


@app.post("/score")
async def score_position(
    score_req: ScoreRequest, utm_source: Union[str, None] = None, utm_campaign: Union[str, None] = None
):
    try:
        query_embedding = calculate_embedding(score_req.position)
        label, score = get_most_similar_label(query_embedding)
    except Exception as e:
        print(e)
        raise HTTPException(500, "Please try again later")

    if label is None:
        print("No labels found in redis")
        raise HTTPException(400, "Could not find any cv's that you might be interested in, come back later")

    asyncio.create_task(save_query_position(score_req.position, score, label.id))

    if score < min_similarity_score:
        raise HTTPException(
            400,
            "Ooops, similarity between your input and my possible positions must be more than {:0.0f}%, try harder or check out the repository".format(
                min_similarity_score * 100
            ),
        )

    score_int = round(score * 100)
    return {
        "token": encrypt_label_id(label.id),
        "detail": f"You got {score_int}% similarity with one of my positions, click OK to get my CV",
        "score": score_int,
    }


@app.post("/download")
async def download(
    request: Request, download_req: DownloadRequest, utm_source: Union[str, None] = None, utm_campaign: Union[str, None] = None
):
    try:
        label_id = decrypt_label_id(download_req.token)
    except ValueError as e:
        raise HTTPException(400, str(e))

    label = get_label_by_id(label_id)
    if label is None:
        raise HTTPException(404, "Can't find requested cv, try to request once more")

    utm_params = None
    if hasattr(request.state, 'utm_params'):
        utm_params = request.state.utm_params

    asyncio.create_task(save_download_by_label_id(label.id, utm_params=utm_params))
    return FileResponse(label.path_to_file, filename=label.file_name, content_disposition_type="attachment")