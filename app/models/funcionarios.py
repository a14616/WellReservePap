"""Modelos de funcionários."""
from django.db import models

from .utilizadores import Utilizador


class HorarioFuncionario(models.Model):
	"""
	Horários de disponibilidade dos funcionários
	"""
	ESTADO_CHOICES = [
		('pendente', 'Pendente'),
		('aprovado', 'Aprovado'),
		('rejeitado', 'Rejeitado'),
	]

	DIAS_SEMANA = [
		(0, 'Segunda-feira'),
		(1, 'Terça-feira'),
		(2, 'Quarta-feira'),
		(3, 'Quinta-feira'),
		(4, 'Sexta-feira'),
		(5, 'Sábado'),
		(6, 'Domingo'),
	]

	funcionario = models.ForeignKey(
		Utilizador,
		on_delete=models.CASCADE,
		limit_choices_to={'tipo__in': ['funcionario', 'recepcao']},
		related_name='horarios',
		verbose_name='Funcionário'
	)
	dia_semana = models.IntegerField(
		choices=DIAS_SEMANA,
		verbose_name='Dia da Semana'
	)
	hora_inicio = models.TimeField(verbose_name='Hora de Início')
	hora_fim = models.TimeField(verbose_name='Hora de Fim')
	ativo = models.BooleanField(default=True, verbose_name='Ativo')
	estado = models.CharField(
		max_length=20,
		choices=ESTADO_CHOICES,
		default='aprovado',
		verbose_name='Estado'
	)

	class Meta:
		verbose_name = 'Horário de Funcionário'
		verbose_name_plural = 'Horários de Funcionários'
		ordering = ['funcionario', 'dia_semana', 'hora_inicio']
		unique_together = ['funcionario', 'dia_semana', 'hora_inicio']

	def __str__(self):
		return f"{self.funcionario.get_full_name()} - {self.get_dia_semana_display()} ({self.hora_inicio} - {self.hora_fim})"


class FeriasFuncionario(models.Model):
	"""
	Períodos de férias ou indisponibilidade dos funcionários
	"""
	ESTADO_CHOICES = [
		('pendente', 'Pendente'),
		('aprovado', 'Aprovado'),
		('rejeitado', 'Rejeitado'),
	]

	funcionario = models.ForeignKey(
		Utilizador,
		on_delete=models.CASCADE,
		limit_choices_to={'tipo__in': ['funcionario', 'recepcao']},
		related_name='ferias',
		verbose_name='Funcionário'
	)
	data_inicio = models.DateField(verbose_name='Data de Início')
	data_fim = models.DateField(verbose_name='Data de Fim')
	motivo = models.CharField(max_length=200, blank=True, verbose_name='Motivo')
	estado = models.CharField(
		max_length=20,
		choices=ESTADO_CHOICES,
		default='aprovado',
		verbose_name='Estado'
	)

	class Meta:
		verbose_name = 'Férias/Indisponibilidade'
		verbose_name_plural = 'Férias/Indisponibilidades'
		ordering = ['-data_inicio']

	def __str__(self):
		return f"{self.funcionario.get_full_name()} - {self.data_inicio} a {self.data_fim}"
