"""Services de produtos da WellReserve."""
from ..models import Produto


class ProdutoService:
    """Operações associadas a produtos."""

    @staticmethod
    def reduzir_stock(produto: Produto, quantidade: int):
        produto.stock = max(0, produto.stock - int(quantidade))
        produto.save(update_fields=['stock'])
        return produto.stock

    @staticmethod
    def calcular_total_carrinho(carrinho_session):
        itens = 0
        total = 0

        for produto_id, quantidade in carrinho_session.items():
            itens += int(quantidade)
            try:
                produto = Produto.objects.get(pk=produto_id, ativo=True)
                total += produto.preco * int(quantidade)
            except Produto.DoesNotExist:
                continue

        return {'itens': itens, 'total': total}
