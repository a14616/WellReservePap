"""Modelos de contactos."""
from django.db import models


class Contacto(models.Model):
	"""
	Mensagens de contacto
	"""
	nome = models.CharField(max_length=100, verbose_name='Nome')
	email = models.EmailField(verbose_name='Email')
	telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
	assunto = models.CharField(max_length=200, verbose_name='Assunto')
	mensagem = models.TextField(verbose_name='Mensagem')
	lida = models.BooleanField(default=False, verbose_name='Lida')
	respondida = models.BooleanField(default=False, verbose_name='Respondida')
	data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')

	class Meta:
		verbose_name = 'Contacto'
		verbose_name_plural = 'Contactos'
		ordering = ['-data_criacao']

	def __str__(self):
		return f"{self.nome} - {self.assunto}"
