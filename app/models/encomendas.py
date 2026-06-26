"""Modelos de encomendas."""
from django.core.validators import MinValueValidator
from django.db import models

from .produtos import Produto
from .utilizadores import Utilizador


class Encomenda(models.Model):
	"""
	Encomendas de produtos
	"""
	ESTADO_CHOICES = [
		('pendente', 'Pendente'),
		('preparacao', 'Em Preparação'),
		('enviada', 'Enviada'),
		('pronta', 'Pronta para Levantamento'),
		('concluida', 'Concluída'),
		('cancelada', 'Cancelada'),
	]
	METODO_PAGAMENTO_CHOICES = [
		('simulado', 'Pagamento Simulado'),
		('rececao', 'Pagamento na Receção'),
	]
	ESTADO_PAGAMENTO_CHOICES = [
		('pendente', 'Pendente'),
		('pago', 'Pago'),
		('falhado', 'Falhado'),
		('reembolsado', 'Reembolsado'),
	]

	cliente = models.ForeignKey(
		Utilizador,
		on_delete=models.CASCADE,
		related_name='encomendas',
		verbose_name='Cliente'
	)
	estado = models.CharField(
		max_length=20,
		choices=ESTADO_CHOICES,
		default='pendente',
		verbose_name='Estado'
	)
	total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Total (€)')
	notas = models.TextField(blank=True, verbose_name='Notas')
	faturacao_nome = models.CharField(max_length=200, blank=True, verbose_name='Nome de Faturação')
	faturacao_email = models.EmailField(blank=True, verbose_name='Email de Faturação')
	faturacao_nif = models.CharField(max_length=20, blank=True, verbose_name='NIF')
	faturacao_morada = models.TextField(blank=True, verbose_name='Morada de Faturação')
	entrega_morada = models.TextField(blank=True, verbose_name='Morada de Entrega')
	metodo_pagamento = models.CharField(
		max_length=20,
		choices=METODO_PAGAMENTO_CHOICES,
		default='simulado',
		verbose_name='Método de Pagamento'
	)
	estado_pagamento = models.CharField(
		max_length=20,
		choices=ESTADO_PAGAMENTO_CHOICES,
		default='pendente',
		verbose_name='Estado de Pagamento'
	)
	referencia_pagamento = models.CharField(max_length=50, blank=True, verbose_name='Referência de Pagamento')
	numero_fatura = models.CharField(max_length=30, blank=True, verbose_name='Número da Fatura')
	data_pagamento = models.DateTimeField(null=True, blank=True, verbose_name='Data de Pagamento')
	data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
	data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

	class Meta:
		verbose_name = 'Encomenda'
		verbose_name_plural = 'Encomendas'
		ordering = ['-data_criacao']

	def __str__(self):
		return f"Encomenda #{self.pk} - {self.cliente.get_full_name()} - {self.total}€"

	def calcular_total(self):
		total = sum(item.subtotal for item in self.itens.all())
		self.total = total
		self.save()
		return total


class ItemEncomenda(models.Model):
	"""
	Itens de uma encomenda
	"""
	encomenda = models.ForeignKey(
		Encomenda,
		on_delete=models.CASCADE,
		related_name='itens',
		verbose_name='Encomenda'
	)
	produto = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name='Produto')
	quantidade = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Quantidade')
	preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Unitário')

	class Meta:
		verbose_name = 'Item de Encomenda'
		verbose_name_plural = 'Itens de Encomenda'

	def __str__(self):
		return f"{self.quantidade}x {self.produto.nome}"

	@property
	def subtotal(self):
		return self.quantidade * self.preco_unitario

	def save(self, *args, **kwargs):
		if not self.preco_unitario:
			self.preco_unitario = self.produto.preco
		super().save(*args, **kwargs)
