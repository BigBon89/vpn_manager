import random
import string

from aiogram.client.session import aiohttp


class ApiPasteEe:
    @staticmethod
    async def create_post(text: str) -> str | None:
        url = "https://paste.ee/paste"
        data = {
            "_token": ApiPasteEe._generate_random_string(),  # 9eo6Z4scyxPixSgEG0QB5V8VDzvUSvgYuMcH6Qgg
            "expiration": "2592000",
            "expiration_views": "",
            "description": "",
            "paste[section1][name]": "",
            "paste[section1][syntax]": "1c",
            "paste[section1][contents]": text,
            "fixlines": "true",
            "jscheck": "validated",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    response_text = await response.text()
                    if "https://paste.ee/p/" in response_text:
                        start_index = response_text.find("https://paste.ee/p/")
                        end_index = response_text.find('"', start_index)
                        paste_url = response_text[start_index:end_index]
                        return paste_url.replace("/p/", "/r/")
                    return None
                return None

    @staticmethod
    def _generate_random_string(length=40):
        characters = string.ascii_letters + string.digits
        return "".join(random.choices(characters, k=length))
