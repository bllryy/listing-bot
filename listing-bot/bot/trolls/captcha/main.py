import numpy as np
import random
import string
from PIL import ImageFont, ImageDraw, Image
import Augmentor
import os
import tempfile
import uuid

def captcha():

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_image_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")

        image = Image.fromarray(np.full((100, 350, 3), 255, dtype=np.uint8))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("bot/trolls/captcha/Captcha Font.ttf", 60)

        text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        W, H = image.size
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        w, h = (right - left, bottom - top)
        draw.text(((W - w) / 2, (H - h) / 2), text, font=font, fill=(90, 90, 90))

        image.save(temp_image_path)

        p = Augmentor.Pipeline(temp_dir)
        p.random_distortion(probability=1, grid_width=4, grid_height=4, magnitude=14)
        p.process()

        distorted_image_path = os.path.join(temp_dir, "output", os.listdir(os.path.join(temp_dir, "output"))[0])
        image = Image.open(distorted_image_path)

        draw = ImageDraw.Draw(image)
        width = random.randrange(6, 8)
        coords = [
            (random.randrange(0, 75), random.randrange(40, 65)),
            (random.randrange(275, 350), random.randrange(40, 65))
        ]
        draw.line(coords, width=width, fill=(90, 90, 90))

        data = np.array(image)
        mask = np.random.rand(*data.shape[:2]) < .25
        data[mask] = (90, 90, 90)
        image = Image.fromarray(data)

    return image, text

if __name__ == "__main__":
    image, text = captcha()
    image.show()