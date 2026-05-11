import asyncio
from playwright.async_api import async_playwright

async def generar_pdf():

    browser = await playwright.chromium.launch()

    page = await browser.new_page()

    await page.goto(
        "file:///Users/urielmeneses/Desktop/MicroservicioPython/ficha_OC310170.html"
    )

    await page.pdf(
        path="ficha_OC310170.pdf",

        format="A4",

        print_background=True,

        margin={
            "top": "20px",
            "right": "20px",
            "bottom": "20px",
            "left": "20px"
        }
    )

    await browser.close()

async def main():

    global playwright

    async with async_playwright() as p:

        playwright = p

        await generar_pdf()

asyncio.run(main())