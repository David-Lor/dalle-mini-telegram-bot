import base64
import pathlib
from typing import List

import pydantic


class DalleResponse(pydantic.BaseModel):
    # Fields returned from API response
    images: List[str] = pydantic.Field(..., min_items=9, max_items=9)  # images as base64 strings

    # Fields we complete
    prompt: str

    @property
    def images_bytes(self):
        images_parsed: List[bytes] = list()
        for image_base64 in self.images:
            images_parsed.append(base64.b64decode(image_base64))
        return images_parsed

    def save_images(self, directory: str):
        directory_path = pathlib.Path(directory)
        for i, image_data in enumerate(self.images_bytes, start=1):
            image_filename = f"{self.prompt} - {i}.jpg"
            image_path = directory_path / image_filename
            with open(image_path, "wb") as f:
                f.write(image_data)
