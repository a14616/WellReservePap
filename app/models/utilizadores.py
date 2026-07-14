"""Modelo de utilizadores."""
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db import models


AnonymousUser.is_admin = property(lambda self: False)
AnonymousUser.is_funcionario = property(lambda self: False)
AnonymousUser.is_cliente = property(lambda self: False)
AnonymousUser.is_recepcao = property(lambda self: False)


class Utilizador(AbstractUser):
	"""
	Modelo de Utilizador personalizado com diferentes níveis de acesso
	"""
	TIPO_CHOICES = [
		('admin', 'Administrador'),
		('recepcao', 'Receção'),
		('funcionario', 'Funcionário'),
		('cliente', 'Cliente'),
	]

	tipo = models.CharField(
		max_length=20,
		choices=TIPO_CHOICES,
		default='cliente',
		verbose_name='Tipo de Utilizador'
	)
	telefone = models.CharField(
		max_length=20,
		blank=True,
		null=True,
		verbose_name='Telefone'
	)
	morada = models.TextField(
		blank=True,
		null=True,
		verbose_name='Morada'
	)
	data_nascimento = models.DateField(
		blank=True,
		null=True,
		verbose_name='Data de Nascimento'
	)
	nif = models.CharField(
		max_length=9,
		blank=True,
		null=True,
		verbose_name='NIF'
	)
	foto = models.ImageField(
		upload_to='utilizadores/',
		blank=True,
		null=True,
		verbose_name='Foto de Perfil'
	)
	data_criacao = models.DateTimeField(
		auto_now_add=True,
		verbose_name='Data de Criação'
	)
	data_atualizacao = models.DateTimeField(
		auto_now=True,
		verbose_name='Última Atualização'
	)

	class Meta:
		verbose_name = 'Utilizador'
		verbose_name_plural = 'Utilizadores'
		ordering = ['-data_criacao']

	def __str__(self):
		return f"{self.get_full_name() or self.username} ({self.get_tipo_display()})"

	@property
	def is_admin(self):
		return self.tipo == 'admin' or self.is_superuser

	@property
	def is_funcionario(self):
		return self.tipo == 'funcionario'

	@property
	def is_cliente(self):
		return self.tipo == 'cliente'

	@property
	def is_recepcao(self):
		return self.tipo == 'recepcao'
