"""MOCK SERVER
Provides mocked endpoints with the same definition as those used by the bot, but returning fake data.
For testing purposes, without performing real requests.
"""

import io
import time
import base64
import random
import typing

import fastapi
import uvicorn
import pydantic
import qrcode
import wait4it


class Settings(pydantic.BaseSettings):
    server_host: str = "0.0.0.0"
    server_port: typing.Optional[int] = None


class Const:
    class DalleMiniGenerate:
        images_n = 9
        images_side_size = 400


class DalleMiniGenerateRequestBody(pydantic.BaseModel):
    prompt: str


class DalleMiniGenerateResponseBody(pydantic.BaseModel):
    images: typing.List[str]  # images as base64 strings


app = fastapi.FastAPI()
settings = Settings()


@app.post("/generate")
def dallemini_generate(
        request_body: DalleMiniGenerateRequestBody, delay: typing.Optional[float] = None
) -> DalleMiniGenerateResponseBody:
    """Mock of DalleMini's /generate endpoint.

    Returns N square images with a QR code, whose data is a JSON with the format:
    ```json
    {"prompt": "<requestbody prompt>", "index": "<index of the image>"}
    ```

    A request delay can be specified through query param; if not set, a random delay between 0~10s will be applied.
    """

    if delay is None:
        delay = random.uniform(0, 10)

    time.sleep(delay)

    images_b64 = list()
    for index in range(Const.DalleMiniGenerate.images_n):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
        )
        qr.add_data({
            "prompt": request_body.prompt,
            "index": index,
        })
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_io = io.BytesIO()
        img.save(img_io)

        img_bytes = img_io.getvalue()
        images_b64.append(base64.b64encode(img_bytes).decode())
        img_io.close()

    return DalleMiniGenerateResponseBody(images=images_b64)


def main():
    if not settings.server_port:
        settings.server_port = wait4it.get_free_port()

    uvicorn.run(
        app=app,
        host=settings.server_host,
        port=settings.server_port,
    )


if __name__ == '__main__':
    main()
