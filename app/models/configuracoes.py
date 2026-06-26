"""Modelos de configurações."""
from django.db import models


class Configuracao(models.Model):
	"""
	Configurações gerais do sistema
	"""
	chave = models.CharField(max_length=100, unique=True, verbose_name='Chave')
	valor = models.TextField(verbose_name='Valor')
	descricao = models.CharField(max_length=200, blank=True, verbose_name='Descrição')

	class Meta:
		verbose_name = 'Configuração'
		verbose_name_plural = 'Configurações'

	def __str__(self):
		return f"{self.chave}: {self.valor}"

	@classmethod
	def get_valor(cls, chave, default=None):
		try:
			return cls.objects.get(chave=chave).valor
		except cls.DoesNotExist:
			return default
