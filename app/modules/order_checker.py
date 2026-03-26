from dataclasses import dataclass, field

from app.clients.piedadmin import PedidoDetalhe
from app.modules.xlsx_parser import XlsParseResult


@dataclass
class ItemDivergencia:
    sku: str
    description_xls: str
    qty_xls: int
    qty_api: int | None  # None = SKU não encontrado na API


@dataclass
class CheckResult:
    order_code: str
    filename_code: str
    cell_code: str
    codes_match: bool
    total_xls: int
    total_api: int
    counts_match: bool  # total de SKUs distintos
    divergencias: list[ItemDivergencia] = field(default_factory=list)

    @property
    def is_correct(self) -> bool:
        return self.codes_match and not self.divergencias


# SKUs cujas quantidades da API vêm em rolos de 25m — multiplica para comparar em metros
_SKU_MULTIPLIER: dict[str, int] = {
    "44": 25,
    "45": 25,
    "46": 25,
    "47": 25,
}


def check_order(xls: XlsParseResult, pedido: PedidoDetalhe) -> CheckResult:
    """
    Compara os itens do XLS com os produtos retornados pela API.
    Verifica:
      1. Código do arquivo == código da célula A1
      2. Todos os SKUs do XLS existem no pedido da API
      3. Quantidade de cada SKU confere
    """
    # Monta índice da API: sku -> (qty, name)
    api_index: dict[str, tuple[int, str]] = {
        p.sku: (p.quantity, p.name) for p in pedido.products
    }

    divergencias: list[ItemDivergencia] = []

    for item in xls.items:
        sku = item["sku"]
        qty_xls = item["quantity"]

        if sku not in api_index:
            divergencias.append(
                ItemDivergencia(
                    sku=sku,
                    description_xls=item["description"],
                    qty_xls=qty_xls,
                    qty_api=None,
                )
            )
        else:
            qty_api_raw, _ = api_index[sku]
            qty_api = qty_api_raw * _SKU_MULTIPLIER.get(sku, 1)
            if qty_xls != qty_api:
                divergencias.append(
                    ItemDivergencia(
                        sku=sku,
                        description_xls=item["description"],
                        qty_xls=qty_xls,
                        qty_api=qty_api,
                    )
                )

    return CheckResult(
        order_code=pedido.code,
        filename_code=xls.filename_code,
        cell_code=xls.cell_code,
        codes_match=xls.codes_match,
        total_xls=len(xls.items),
        total_api=len(pedido.products),
        counts_match=(len(xls.items) == len(pedido.products)),
        divergencias=divergencias,
    )
