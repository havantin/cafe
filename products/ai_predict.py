from PIL import Image
import random

def predict_image(path):

    img = Image.open(path)

    # AI giả lập
    foods = [
        "Cà phê sữa",
        "Cà phê đen",
        "Bạc xỉu",
        "Trà sữa",
        "Matcha latte"
    ]

    return random.choice(foods)