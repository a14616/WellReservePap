"""Vistas de produtos e carrinho."""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .auth import admin_required, login_required
from ..content_assets import produto_assets
from ..forms import ProdutoForm
from ..models import CategoriaProduto, Produto


def _enrich_products(produtos):
	for produto in produtos:
		assets = produto_assets(produto)
		produto.imagem_capa = produto.imagem.url if getattr(produto, 'imagem', None) else assets['cover']
		produto.galeria_imagens = assets['gallery']
	return produtos


def produtos_lista(request):
	"""Lista de produtos"""
	categoria_id = request.GET.get('categoria')

	produtos = Produto.objects.filter(ativo=True).select_related('categoria')

	if categoria_id:
		produtos = produtos.filter(categoria_id=categoria_id)

	categorias = CategoriaProduto.objects.filter(ativo=True)
	produtos = _enrich_products(list(produtos))

	context = {
		'produtos': produtos,
		'categorias': categorias,
		'categoria_selecionada': int(categoria_id) if categoria_id else None,
	}
	return render(request, 'produtos/lista.html', context)


def produto_detalhe(request, pk):
	"""Detalhe de um produto"""
	produto = get_object_or_404(Produto, pk=pk, ativo=True)
	produto = _enrich_products([produto])[0]
	produtos_relacionados = _enrich_products(list(Produto.objects.filter(categoria=produto.categoria, ativo=True).exclude(pk=pk)[:4]))

	context = {
		'produto': produto,
		'produtos_relacionados': produtos_relacionados,
	}
	return render(request, 'produtos/detalhe.html', context)


@admin_required
def produtos_gestao(request):
	"""Gestão de produtos (admin)"""
	produtos = Produto.objects.select_related('categoria').all()
	pesquisa = request.GET.get('q', '').strip()
	categoria_id = request.GET.get('categoria', '').strip()
	ativo = request.GET.get('ativo', '').strip()

	if pesquisa:
		produtos = produtos.filter(
			Q(nome__icontains=pesquisa) |
			Q(descricao__icontains=pesquisa)
		)
	if categoria_id:
		produtos = produtos.filter(categoria_id=categoria_id)
	if ativo in ['0', '1']:
		produtos = produtos.filter(ativo=(ativo == '1'))

	produtos = produtos.order_by('categoria__nome', 'nome')
	categorias = CategoriaProduto.objects.all()

	context = {
		'produtos': produtos,
		'categorias': categorias,
	}
	return render(request, 'gestao/produtos.html', context)


@admin_required
def produto_criar(request):
	"""Criar novo produto"""
	if request.method == 'POST':
		form = ProdutoForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			messages.success(request, 'Produto criado com sucesso!')
			return redirect('produtos_gestao')
	else:
		form = ProdutoForm()

	return render(request, 'gestao/produto_form.html', {'form': form, 'titulo': 'Criar Produto'})


@admin_required
def produto_editar(request, pk):
	"""Editar produto"""
	produto = get_object_or_404(Produto, pk=pk)

	if request.method == 'POST':
		form = ProdutoForm(request.POST, request.FILES, instance=produto)
		if form.is_valid():
			form.save()
			messages.success(request, 'Produto atualizado com sucesso!')
			return redirect('produtos_gestao')
	else:
		form = ProdutoForm(instance=produto)

	return render(request, 'gestao/produto_form.html', {'form': form, 'titulo': 'Editar Produto', 'produto': produto})


@admin_required
def produto_eliminar(request, pk):
	"""Eliminar produto"""
	produto = get_object_or_404(Produto, pk=pk)

	if request.method == 'POST':
		produto.delete()
		messages.success(request, 'Produto eliminado com sucesso!')
		return redirect('produtos_gestao')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': produto,
		'tipo': 'produto',
		'voltar_url': 'produtos_gestao'
	})


def carrinho(request):
	"""Ver carrinho de compras"""
	carrinho_session = request.session.get('carrinho', {})
	itens = []
	total = 0

	for produto_id, quantidade in carrinho_session.items():
		try:
			produto = Produto.objects.get(pk=produto_id, ativo=True)
			subtotal = produto.preco * quantidade
			itens.append({'produto': produto, 'quantidade': quantidade, 'subtotal': subtotal})
			total += subtotal
		except Produto.DoesNotExist:
			pass

	context = {
		'carrinho': itens,
		'total': total,
	}
	return render(request, 'produtos/carrinho.html', context)


def carrinho_adicionar(request, pk):
	"""Adicionar produto ao carrinho"""
	produto = get_object_or_404(Produto, pk=pk, ativo=True)

	if not produto.disponivel:
		messages.error(request, 'Este produto não está disponível.')
		return redirect('produto_detalhe', pk=pk)

	carrinho_session = request.session.get('carrinho', {})
	produto_id = str(pk)

	try:
		quantidade = int(request.POST.get('quantidade', 1))
	except (TypeError, ValueError):
		quantidade = 1

	quantidade = max(1, min(quantidade, produto.stock))

	if produto_id in carrinho_session:
		carrinho_session[produto_id] += quantidade
	else:
		carrinho_session[produto_id] = quantidade

	request.session['carrinho'] = carrinho_session
	messages.success(request, f'{produto.nome} adicionado ao carrinho!')
	return redirect('carrinho')


@login_required
def carrinho_remover(request, pk):
	"""Remover produto do carrinho"""
	carrinho_session = request.session.get('carrinho', {})
	produto_id = str(pk)

	if produto_id in carrinho_session:
		del carrinho_session[produto_id]
		request.session['carrinho'] = carrinho_session
		messages.success(request, 'Produto removido do carrinho.')

	return redirect('carrinho')


def carrinho_atualizar(request):
	"""Atualizar quantidades do carrinho"""
	if request.method == 'POST':
		carrinho_session = request.session.get('carrinho', {})
		acao = request.POST.get('acao')
		produto_id = request.POST.get('produto_id')

		if acao and produto_id:
			try:
				produto = Produto.objects.get(pk=produto_id, ativo=True)
			except Produto.DoesNotExist:
				produto = None

			current = int(carrinho_session.get(str(produto_id), 0))
			if acao == 'aumentar':
				if produto and produto.disponivel:
					novo = min(current + 1, produto.stock)
				else:
					novo = current + 1
				carrinho_session[str(produto_id)] = max(1, novo)
			elif acao == 'diminuir':
				novo = current - 1
				if novo > 0:
					carrinho_session[str(produto_id)] = novo
				elif str(produto_id) in carrinho_session:
					del carrinho_session[str(produto_id)]

			request.session['carrinho'] = carrinho_session
			messages.success(request, 'Carrinho atualizado!')
			return redirect('carrinho')

		for key, value in request.POST.items():
			if key.startswith('quantidade_'):
				produto_id = key.replace('quantidade_', '')
				try:
					quantidade = int(value)
					if quantidade > 0:
						carrinho_session[produto_id] = quantidade
					elif produto_id in carrinho_session:
						del carrinho_session[produto_id]
				except (ValueError, KeyError):
					pass

		request.session['carrinho'] = carrinho_session
		messages.success(request, 'Carrinho atualizado!')

	return redirect('carrinho')


def carrinho_limpar(request):
	"""Limpar todo o carrinho da sessão"""
	if request.method == 'POST':
		if 'carrinho' in request.session:
			try:
				del request.session['carrinho']
			except KeyError:
				pass
		messages.success(request, 'Carrinho limpo.')
	return redirect('carrinho')
