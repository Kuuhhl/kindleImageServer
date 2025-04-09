import os
import io
import asyncio
import requests
from flask import Flask, send_file, current_app
from jinja2 import Template
from async_lru import alru_cache
from playwright.async_api import async_playwright
from PIL import Image

app = Flask(__name__)

ENTITY_ID = os.environ.get("SENSOR_NAME")
PORT = 5000
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")

def get_dashboard_message():
    try:
        headers = {
            "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"http://supervisor/core/api/states/{ENTITY_ID}",
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return response.json()["state"]
    except Exception as e:
        current_app.logger.error(f"[ERROR] Failed to fetch from Home Assistant: {e}")
        return "Unavailable"

@app.route("/image")
def render_image():
    # Run the asynchronous function, get raw image bytes, then wrap them in a new BytesIO.
    image_bytes = asyncio.run(render_dashboard_cached(get_dashboard_message()))
    return send_file(io.BytesIO(image_bytes), mimetype="image/png")

@alru_cache(maxsize=10)
async def render_dashboard_cached(message):
    # Read and render the template
    try:
        with open("dashboard.html") as f:
            template = Template(f.read())
    except FileNotFoundError:
        current_app.logger.error("[ERROR] dashboard.html file not found.")
        return b""

    html = template.render(message=message)
    screenshot_path = "/tmp/output.png"

    # Use Playwright to create a screenshot
    async with async_playwright() as p:
        browser = await p.firefox.launch()
        page = await browser.new_page(viewport={"width": 1072, "height": 1448})
        await page.set_content(html)
        await page.screenshot(path=screenshot_path)
        await browser.close()

    # convert to grayscale
    with Image.open(screenshot_path) as img:
        bw_img = img.convert("L")
        buffer = io.BytesIO()
        bw_img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

    return image_bytes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
