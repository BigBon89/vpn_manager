import base64
import json
from datetime import timedelta, datetime, timezone

from api3x import Api3x
from apipasteee import ApiPasteEe
from database.database import Database


class Server:
    def __init__(
            self,
            flag: str,
            country: str,
            city: str,
            login: str,
            password: str,
            ip: str,
            port: str,
            base: str,
            sid: str,
            pbk: str
    ) -> None:
        self.flag = flag
        self.country = country
        self.city = city
        self.login = login
        self.password = password
        self.ip = ip
        self.port = port
        self.base = base
        self.sid = sid
        self.pbk = pbk


class Servers:
    def __init__(self) -> None:
        self.servers: list[Server] = []

    def add_server(self, server: Server) -> None:
        self.servers.append(server)


class Plan:
    def __init__(self, name: str, price: int) -> None:
        self.name = name
        self.price = price


class Plans:
    def __init__(self) -> None:
        self.plans: list[Plan] = []

    def add_plan(self, plan: Plan) -> None:
        self.plans.append(plan)


class Core:
    def __init__(self, config_path: str = "config.json") -> None:
        self.servers = Servers()
        self.plans = Plans()
        self.db = Database()
        self.bot_token = ""
        self.crypto_pay_token = ""
        self.admin_id = 0
        self._load_config(config_path)

    async def _generate_links(self, email: str) -> str:
        result = ""
        for server in self.servers.servers:
            uid = await Api3x.get_uid_from_email(
                server.ip, server.port, server.base, server.login, server.password, email
            )
            result += (
                f"vless://{uid}@{server.ip}:443?"
                f"type=tcp&"
                f"security=reality&"
                f"pbk={server.pbk}&"
                f"fp=chrome&"
                f"sni=ya.ru&"
                f"sid={server.sid}&"
                f"spx=%2F&"
                f"flow=xtls-rprx-vision#"
                f"{server.flag} {server.country}\n"
            )
        return result

    async def create_url(self, email: str) -> str | None:
        links = await self._generate_links(email)
        encoded = base64.b64encode(links.encode("utf-8")).decode("utf-8")
        return f"{await ApiPasteEe.create_post(encoded)}#Ferrari_VPN"

    async def delete_depleted_clients(self) -> bool:
        result = True
        for server in self.servers.servers:
            if (not await Api3x.delete_depleted_clients(
                    ip=server.ip,
                    port=server.port,
                    base=server.base,
                    username=server.login,
                    password=server.password
            )):
                result = False
        return result

    async def add_key(self, tg_id: int, days: int) -> bool:
        await self.delete_depleted_clients()
        self.db.delete_depleted_keys()

        key = self.db.get_key_from_tg_id(tg_id)
        if key is None:
            end = (datetime.now(timezone.utc) + timedelta(hours=3) + timedelta(days=days)).replace(microsecond=0)
            self.db.add_key(tg_id, end, await self.create_url(str(tg_id)))
        else:
            end = (key.end + timedelta(days=days)).replace(microsecond=0)
            self.db.update_key_end(tg_id, end)

        for server in self.servers.servers:
            await Api3x.create_or_update_client(
                ip=server.ip,
                port=server.port,
                base=server.base,
                username=server.login,
                password=server.password,
                email=str(tg_id),
                expiry_time=int(end.timestamp()) * 1000
            )

        return True

    async def update_key(self, tg_id: int) -> bool:
        key = self.db.get_key_from_tg_id(tg_id)
        if key is None:
            return False
        for server in self.servers.servers:
            await Api3x.create_or_update_client(
                ip=server.ip,
                port=server.port,
                base=server.base,
                username=server.login,
                password=server.password,
                email=str(tg_id),
                expiry_time=int(key.end.timestamp()) * 1000
            )
        self.db.update_key_url(tg_id, await self.create_url(str(tg_id)))
        return True

    def _load_config(self, config_path: str) -> None:
        with open(config_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        for server_id, server_data in data["servers"].items():
            server = Server(
                flag=server_data["flag"],
                country=server_data["country"],
                city=server_data["city"],
                login=server_data["login"],
                password=server_data["password"],
                ip=server_data["ip"],
                port=server_data["port"],
                base=server_data["base"],
                sid=server_data["sid"],
                pbk=server_data["pbk"]
            )
            self.servers.add_server(server)

        for plan_name, price in data["plans"].items():
            plan = Plan(name=plan_name, price=price)
            self.plans.add_plan(plan)
