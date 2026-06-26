"""Modelos de reservas."""
from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

from .servicos import Servico
from .utilizadores import Utilizador


class Reserva(models.Model):
	"""
	Reservas de serviços
	"""
	ESTADO_CHOICES = [
		('pendente', 'Pendente'),
		('confirmada', 'Confirmada'),
		('cancelada', 'Cancelada'),
		('concluida', 'Concluída'),
		('nao_compareceu', 'Não Compareceu'),
	]

	cliente = models.ForeignKey(
		Utilizador,
		on_delete=models.CASCADE,
		limit_choices_to={'tipo': 'cliente'},
		related_name='reservas',
		verbose_name='Cliente'
	)
	servico = models.ForeignKey(
		Servico,
		on_delete=models.CASCADE,
		related_name='reservas',
		verbose_name='Serviço'
	)
	funcionario = models.ForeignKey(
		Utilizador,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		limit_choices_to={'tipo': 'funcionario'},
		related_name='reservas_atribuidas',
		verbose_name='Funcionário'
	)
	data = models.DateField(verbose_name='Data')
	hora = models.TimeField(verbose_name='Hora')
	estado = models.CharField(
		max_length=20,
		choices=ESTADO_CHOICES,
		default='pendente',
		verbose_name='Estado'
	)
	notas = models.TextField(blank=True, verbose_name='Notas')
	notas_internas = models.TextField(blank=True, verbose_name='Notas Internas (Staff)')
	preco_final = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		null=True,
		blank=True,
		verbose_name='Preço Final'
	)
	data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
	data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

	class Meta:
		verbose_name = 'Reserva'
		verbose_name_plural = 'Reservas'
		ordering = ['-data', '-hora']

	def __str__(self):
		return f"Reserva #{self.pk} - {self.cliente.get_full_name()} - {self.servico.nome} - {self.data} {self.hora}"

	def save(self, *args, **kwargs):
		if not self.preco_final:
			self.preco_final = self.servico.preco
		super().save(*args, **kwargs)

	@property
	def hora_fim(self):
		inicio = datetime.combine(self.data, self.hora)
		fim = inicio + timedelta(minutes=self.servico.duracao)
		return fim.time()

	@property
	def pode_cancelar(self):
		"""Verifica se a reserva pode ser cancelada (até 24h antes)"""
		agora = timezone.now()
		data_reserva = timezone.make_aware(datetime.combine(self.data, self.hora))
		return (data_reserva - agora) > timedelta(hours=24) and self.estado in ['pendente', 'confirmada']
