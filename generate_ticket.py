from io import BytesIO

import requests
from PIL import Image, ImageFont, ImageDraw

BLANK_PATH = 'image/ticket_blank.png'
FONT_PATH = 'fonts/Roboto-Regular.ttf'
FONT_SIZE = 30

COLOR = (0, 0, 0, 255)
NAME_OFFSET = (400, 245)
EMAIL_OFFSET = (400, 285)
AVATAR_SIZE = 100
AVATAR_OFFSET = (50, 180)
AVATAR = 'image/avatar1.jpg'


def generate_ticket(name, email):
    base = Image.open(BLANK_PATH).convert('RGBA')
    font_for_ticket = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw_obj = ImageDraw.Draw(base)
    draw_obj.text(NAME_OFFSET, name, font=font_for_ticket, fill=COLOR)
    draw_obj.text(EMAIL_OFFSET, email, font=font_for_ticket, fill=COLOR)

    # response = requests.get(url=f'https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}')
    avatar_open = Image.open(AVATAR)
    base.paste(box=AVATAR_OFFSET, im=avatar_open)
    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file

if __name__ == '__main__':
    generate_ticket('DWE', 'mail@mail.ru')