"""Modelos de serviços."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .utilizadores import Utilizador


class CategoriaServico(models.Model):
	"""
	Categorias de serviços
	"""
	nome = models.CharField(
		max_length=100,
		verbose_name='Nome da Categoria'
	)
	descricao = models.TextField(
		blank=True,
		verbose_name='Descrição'
	)
	icone = models.CharField(
		max_length=50,
		blank=True,
		default='fa-layer-group',
		verbose_name='Ícone (FontAwesome)'
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
		verbose_name = 'Categoria de Serviço'
		verbose_name_plural = 'Categorias de Serviços'
		ordering = ['ordem', 'nome']

	def __str__(self):
		return self.nome


class Servico(models.Model):
	"""
	Serviços disponíveis
	"""
	nome = models.CharField(
		max_length=200,
		verbose_name='Nome do Serviço'
	)
	descricao = models.TextField(
		verbose_name='Descrição'
	)
	categoria = models.ForeignKey(
		CategoriaServico,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='servicos',
		verbose_name='Categoria'
	)
	duracao = models.PositiveIntegerField(
		validators=[MinValueValidator(15), MaxValueValidator(480)],
		verbose_name='Duração (minutos)',
		help_text='Duração do serviço em minutos (15-480)'
	)
	preco = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(0)],
		verbose_name='Preço (€)'
	)
	funcionarios = models.ManyToManyField(
		Utilizador,
		limit_choices_to={'tipo': 'funcionario'},
		related_name='servicos_atribuidos',
		blank=True,
		verbose_name='Funcionários Atribuídos'
	)
	imagem = models.ImageField(
		upload_to='servicos/',
		blank=True,
		null=True,
		verbose_name='Imagem'
	)
	capacidade_maxima = models.PositiveIntegerField(
		default=1,
		validators=[MinValueValidator(1)],
		verbose_name='Capacidade Máxima',
		help_text='Número máximo de clientes por sessão'
	)
	requer_prescricao = models.BooleanField(
		default=False,
		verbose_name='Requer Validação Prévia'
	)
	ativo = models.BooleanField(
		default=True,
		verbose_name='Ativo'
	)
	destaque = models.BooleanField(
		default=False,
		verbose_name='Em Destaque'
	)
	is_aula = models.BooleanField(
		default=False,
		verbose_name='Aula',
		help_text='Marcar se este serviço é uma aula (horários fixos ou reservas ad-hoc)'
	)
	data_criacao = models.DateTimeField(
		auto_now_add=True,
		verbose_name='Data de Criação'
	)

	class Meta:
		verbose_name = 'Serviço'
		verbose_name_plural = 'Serviços'
		ordering = ['categoria', 'nome']

	def __str__(self):
		return f"{self.nome} - {self.duracao}min - {self.preco}€"

	@property
	def duracao_formatada(self):
		horas = self.duracao // 60
		minutos = self.duracao % 60
		if horas > 0:
			return f"{horas}h {minutos}min" if minutos > 0 else f"{horas}h"
		return f"{minutos}min"


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

	servico = models.ForeignKey(
		Servico,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name='horarios_servico',
		verbose_name='Serviço'
	)
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
	hora_inicio = models.TimeField(
		verbose_name='Hora de Início'
	)
	hora_fim = models.TimeField(
		verbose_name='Hora de Fim'
	)
	data_inicio = models.DateField(
		blank=True,
		null=True,
		verbose_name='Data Início (opcional)'
	)
	data_fim = models.DateField(
		blank=True,
		null=True,
		verbose_name='Data Fim (opcional)'
	)
	ativo = models.BooleanField(
		default=True,
		verbose_name='Ativo'
	)
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
		constraints = [
			models.UniqueConstraint(
				fields=['funcionario', 'dia_semana', 'hora_inicio'],
				condition=models.Q(servico__isnull=True),
				name='uniq_horario_global_funcionario_dia_hora'
			),
			models.UniqueConstraint(
				fields=['servico', 'funcionario', 'dia_semana', 'hora_inicio'],
				condition=models.Q(servico__isnull=False),
				name='uniq_horario_servico_funcionario_dia_hora'
			),
		]

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
	data_inicio = models.DateField(
		verbose_name='Data de Início'
	)
	data_fim = models.DateField(
		verbose_name='Data de Fim'
	)
	motivo = models.CharField(
		max_length=200,
		blank=True,
		verbose_name='Motivo'
	)
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


class BloqueioHorario(models.Model):
	"""
	Bloqueio de horários específicos (ocorrência cancelada) para um funcionário ou para um serviço.
	Permite cancelar uma aula/turno específico sem remover o serviço ou o horário recorrente.
	"""
	funcionario = models.ForeignKey(
		Utilizador,
		on_delete=models.CASCADE,
		limit_choices_to={'tipo__in': ['funcionario', 'recepcao']},
		related_name='bloqueios',
		null=True,
		blank=True,
		verbose_name='Funcionário'
	)
	servico = models.ForeignKey(
		Servico,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name='bloqueios',
		verbose_name='Serviço'
	)
	data = models.DateField(verbose_name='Data')
	hora_inicio = models.TimeField(verbose_name='Hora Início')
	hora_fim = models.TimeField(verbose_name='Hora Fim')
	motivo = models.CharField(max_length=200, blank=True, verbose_name='Motivo')
	criado_em = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Bloqueio de Horário'
		verbose_name_plural = 'Bloqueios de Horários'
		ordering = ['-data', 'hora_inicio']

	def __str__(self):
		target = self.funcionario.get_full_name() if self.funcionario else (self.servico.nome if self.servico else 'Geral')
		return f"Bloqueio: {target} - {self.data} {self.hora_inicio}-{self.hora_fim}"
