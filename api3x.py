import json
import string
import uuid
import random

from aiogram.client.session import aiohttp


class Api3x:
    @staticmethod
    async def _get_cookie(ip: str, port: str, base: str, username: str, password: str) -> str | None:
        url = f"http://{ip}:{port}/{base}/login"
        data = {
            "username": username,
            "password": password
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    cookie = response.cookies.get("3x-ui").value
                    if cookie:
                        return cookie
                    return None
                return None

    @staticmethod
    async def create_client(ip: str, port: str, base: str, username: str, password: str, email: str,
                            expiry_time: int) -> bool:
        cookie = await Api3x._get_cookie(ip, port, base, username, password)
        if cookie is None:
            return False

        url = f"http://{ip}:{port}/{base}/panel/api/inbounds/addClient"
        headers = {
            "Accept": "application/json",
            "Cookie": f"3x-ui={cookie}",
        }
        payload = {
            "id": 1,
            "settings": json.dumps({
                "clients": [
                    {
                        "id": Api3x._generate_id(),
                        "flow": "xtls-rprx-vision",
                        "email": email,
                        "limitIp": 3,
                        "totalGB": 0,
                        "expiryTime": expiry_time,
                        "enable": True,
                        "tgId": "",
                        "subId": Api3x._generate_sub_id(),
                        "reset": 0
                    }
                ]
            })
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return True
                return False

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _generate_sub_id() -> str:
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choices(characters, k=16))

    @staticmethod
    async def get_client_object_from_email(
            ip: str, port: str, base: str, username: str, password: str, email: str
    ) -> dict | None:
        cookie = await Api3x._get_cookie(ip, port, base, username, password)
        if cookie is None:
            return None
        url = f"http://{ip}:{port}/{base}/panel/api/inbounds/get/1"
        headers = {
            "Accept": "application/json",
            "Cookie": f"3x-ui={cookie}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    clients = json.loads(data["obj"]["settings"])["clients"]
                    for client in clients:
                        if client["email"] == email:
                            return client
                    return None
                return None

    @staticmethod
    async def get_uid_from_email(ip: str, port: str, base: str, username: str, password: str, email: str) -> str | None:
        obj = await Api3x.get_client_object_from_email(ip, port, base, username, password, email)
        return None if obj is None else obj["id"]

    @staticmethod
    async def delete_depleted_clients(ip: str, port: str, base: str, username: str, password: str) -> bool:
        cookie = await Api3x._get_cookie(ip, port, base, username, password)
        if cookie is None:
            return False
        url = f"http://{ip}:{port}/{base}/panel/api/inbounds/delDepletedClients/1"
        headers = {
            "Accept": "application/json",
            "Cookie": f"3x-ui={cookie}",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                if response.status == 200:
                    return True
                return False

    @staticmethod
    async def update_client(
            ip: str, port: str, base: str, username: str, password: str, email: str, expiry_time: int
    ) -> bool:
        cookie = await Api3x._get_cookie(ip, port, base, username, password)
        if cookie is None:
            return False
        obj = await Api3x.get_client_object_from_email(ip, port, base, username, password, email)
        if obj is None:
            return False
        url = f"http://{ip}:{port}/{base}/panel/api/inbounds/updateClient/{obj["id"]}"
        headers = {
            "Accept": "application/json",
            "Cookie": f"3x-ui={cookie}",
        }
        payload = {
            "id": 1,
            "settings": json.dumps({
                "clients": [
                    {
                        "id": obj["id"],
                        "flow": obj["flow"],
                        "email": obj["email"],
                        "limitIp": obj["limitIp"],
                        "totalGB": obj["totalGB"],
                        "expiryTime": expiry_time,
                        "enable": obj["enable"],
                        "tgId": obj["tgId"],
                        "subId": obj["subId"],
                        "reset": obj["reset"]
                    }
                ]
            })
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return True
                return False

    @staticmethod
    async def create_or_update_client(
            ip: str, port: str, base: str, username: str, password: str, email: str, expiry_time: int
    ) -> bool:
        cookie = await Api3x._get_cookie(ip, port, base, username, password)
        if cookie is None:
            return False
        obj = await Api3x.get_client_object_from_email(ip, port, base, username, password, email)
        if obj is None:
            return await Api3x.create_client(ip, port, base, username, password, email, expiry_time)
        return await Api3x.update_client(ip, port, base, username, password, email, expiry_time)
