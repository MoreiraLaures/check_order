import httpx
import asyncio
from pydantic import BaseModel


class ProductItem(BaseModel):
    sku: str
    name: str
    quantity: int


class PedidoDetalhe(BaseModel):
    code: str
    name: str
    products: list[ProductItem]


class PiedAdminClient:
    BASE_URL: str = "https://piedadmin.com.br/api/v1"

    def __init__(self, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(15.0),
        )

    async def buscar_pedido(self, code: str) -> PedidoDetalhe:
        response = await self._client.get(
            "/requests/order/0/1",
            params={"code": code},
        )
        response.raise_for_status()
        data = response.json()

        items = data["data"]["items"]
        if not items:
            raise ValueError(f"Pedido '{code}' não encontrado na API.")

        raw = items[0]
        products = [
            ProductItem(
                sku=str(p["productCode"]),
                name=p["name"],
                quantity=int(p["quantity"]),
            )
            for p in raw.get("products", [])
        ]
        return PedidoDetalhe(
            code=raw["code"],
            name=raw["name"],
            products=products,
        )

    async def buscar_varios(self, codes: list[str]) -> list[PedidoDetalhe]:
        return list(await asyncio.gather(*[self.buscar_pedido(c) for c in codes]))

    async def __aenter__(self) -> "PiedAdminClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()
