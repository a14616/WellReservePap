from .models import Produto


def carrinho_summary(request):
    """Context processor que adiciona resumo do carrinho a todos os templates."""
    carrinho_session = request.session.get('carrinho', {})
    itens = 0
    total = 0

    try:
        for produto_id, quantidade in carrinho_session.items():
            itens += int(quantidade)
            try:
                produto = Produto.objects.get(pk=produto_id, ativo=True)
                total += produto.preco * int(quantidade)
            except Produto.DoesNotExist:
                continue
    except Exception:
        itens = 0
        total = 0

    return {
        'carrinho_itens': itens,
        'carrinho_total': total,
    }
