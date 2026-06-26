"""Modelos de produtos."""
from django.core.validators import MinValueValidator
from django.db import models


class CategoriaProduto(models.Model):
	"""
	Categorias de produtos
	"""
	nome = models.CharField(
		max_length=100,
		verbose_name='Nome da Categoria'
	)
	descricao = models.TextField(
		blank=True,
		verbose_name='Descrição'
	)
	ordem = models.PositiveIntegerField(
		default=0,
		verbose_name='Ordem de Exibição'
	)
	ativo = models.BooleanField(
		default=True,
		verbose_name='Ativo'
	)

	class Meta:
		verbose_name = 'Categoria de Produto'
		verbose_name_plural = 'Categorias de Produtos'
		ordering = ['ordem', 'nome']

	def __str__(self):
		return self.nome


class Produto(models.Model):
	"""
	Produtos disponíveis para encomenda
	"""
	nome = models.CharField(max_length=200, verbose_name='Nome do Produto')
	descricao = models.TextField(verbose_name='Descrição')
	categoria = models.ForeignKey(
		CategoriaProduto,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='produtos',
		verbose_name='Categoria'
	)
	preco = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(0)],
		verbose_name='Preço (€)'
	)
	stock = models.PositiveIntegerField(default=0, verbose_name='Stock Disponível')
	imagem = models.ImageField(
		upload_to='produtos/',
		blank=True,
		null=True,
		verbose_name='Imagem'
	)
	ativo = models.BooleanField(default=True, verbose_name='Ativo')
	destaque = models.BooleanField(default=False, verbose_name='Em Destaque')
	data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')

	class Meta:
		verbose_name = 'Produto'
		verbose_name_plural = 'Produtos'
		ordering = ['categoria', 'nome']

	def __str__(self):
		return f"{self.nome} - {self.preco}€"

	@property
	def disponivel(self):
		return self.ativo and self.stock > 0
