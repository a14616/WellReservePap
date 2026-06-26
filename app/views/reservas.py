"""Vistas de reservas."""
from datetime import date, datetime, timedelta
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from .auth import recepcao_funcionario_required
from ..forms import PesquisaReservaForm, ReservaAdminForm, ReservaForm
from ..models import FeriasFuncionario, HorarioFuncionario, Reserva, Servico, Utilizador

logger = logging.getLogger(__name__)


@login_required
def reservas_lista(request):
	"""Lista de reservas do utilizador"""
	if request.user.is_admin or request.user.is_recepcao:
		reservas = Reserva.objects.select_related('cliente', 'servico', 'funcionario').all()
	elif request.user.is_funcionario:
		reservas = Reserva.objects.filter(funcionario=request.user).select_related('cliente', 'servico')
	else:
		reservas = Reserva.objects.filter(cliente=request.user).select_related('servico', 'funcionario')

	form = PesquisaReservaForm(request.GET)
	if form.is_valid():
		if form.cleaned_data.get('data_inicio'):
			reservas = reservas.filter(data__gte=form.cleaned_data['data_inicio'])
		if form.cleaned_data.get('data_fim'):
			reservas = reservas.filter(data__lte=form.cleaned_data['data_fim'])
		if form.cleaned_data.get('estado'):
			reservas = reservas.filter(estado=form.cleaned_data['estado'])
		if form.cleaned_data.get('servico'):
			reservas = reservas.filter(servico=form.cleaned_data['servico'])

	reservas = reservas.order_by('-data', '-hora')

	paginator = Paginator(reservas, 20)
	page = request.GET.get('page')
	reservas = paginator.get_page(page)

	context = {
		'reservas': reservas,
		'form': form,
	}
	return render(request, 'reservas/lista.html', context)


@login_required
def minhas_reservas(request):
	"""Página com as reservas onde o utilizador é o cliente (independentemente do seu papel)"""
	reservas = Reserva.objects.filter(cliente=request.user).select_related('servico', 'funcionario')

	form = PesquisaReservaForm(request.GET)
	if form.is_valid():
		if form.cleaned_data.get('data_inicio'):
			reservas = reservas.filter(data__gte=form.cleaned_data['data_inicio'])
		if form.cleaned_data.get('data_fim'):
			reservas = reservas.filter(data__lte=form.cleaned_data['data_fim'])
		if form.cleaned_data.get('estado'):
			reservas = reservas.filter(estado=form.cleaned_data['estado'])
		if form.cleaned_data.get('servico'):
			reservas = reservas.filter(servico=form.cleaned_data['servico'])

	reservas = reservas.order_by('-data', '-hora')

	paginator = Paginator(reservas, 20)
	page = request.GET.get('page')
	reservas = paginator.get_page(page)

	context = {
		'reservas': reservas,
		'form': form,
	}
	return render(request, 'reservas/lista.html', context)


@login_required
def reservas_funcionario(request, pk):
	"""Lista de reservas de um funcionário específico"""
	funcionario = get_object_or_404(Utilizador, pk=pk, tipo='funcionario')

	if not (request.user.is_admin or request.user.is_recepcao or request.user.pk == pk):
		messages.error(request, 'Não tem permissão para ver estas reservas.')
		return redirect('dashboard')

	reservas = Reserva.objects.filter(funcionario=funcionario).select_related('cliente', 'servico').order_by('-data', '-hora')

	paginator = Paginator(reservas, 20)
	page = request.GET.get('page')
	reservas = paginator.get_page(page)

	context = {
		'reservas': reservas,
		'funcionario': funcionario,
	}
	return render(request, 'reservas/funcionario.html', context)


@login_required
def reserva_criar(request):
	"""Criar nova reserva"""
	servico_id = request.GET.get('servico')
	cliente_id = request.GET.get('cliente')

	if request.method == 'POST':
		if request.user.is_recepcao or request.user.is_admin:
			form = ReservaAdminForm(request.POST)
		else:
			form = ReservaForm(request.POST)

		if form.is_valid():
			reserva = form.save(commit=False)
			if not (request.user.is_recepcao or request.user.is_admin):
				reserva.cliente = request.user
			reserva.save()
			messages.success(request, 'Reserva criada com sucesso! Aguarde confirmação.')
			return redirect('reservas_lista')
	else:
		initial = {}
		if servico_id:
			initial['servico'] = servico_id
		if cliente_id and (request.user.is_recepcao or request.user.is_admin):
			initial['cliente'] = cliente_id

		if request.user.is_recepcao or request.user.is_admin:
			form = ReservaAdminForm(initial=initial)
		else:
			form = ReservaForm(initial=initial)

	return render(request, 'reservas/criar.html', {'form': form})


@login_required
def reserva_detalhe(request, pk):
	"""Detalhe de uma reserva"""
	if request.user.is_admin or request.user.is_recepcao:
		reserva = get_object_or_404(Reserva, pk=pk)
	elif request.user.is_funcionario:
		reserva = get_object_or_404(Reserva, pk=pk, funcionario=request.user)
	else:
		reserva = get_object_or_404(Reserva, pk=pk, cliente=request.user)

	return render(request, 'reservas/detalhe.html', {'reserva': reserva})


@login_required
def reserva_cancelar(request, pk):
	"""Cancelar reserva"""
	if request.user.is_admin or request.user.is_recepcao:
		reserva = get_object_or_404(Reserva, pk=pk)
	else:
		reserva = get_object_or_404(Reserva, pk=pk, cliente=request.user)

	if not reserva.pode_cancelar and not (request.user.is_admin or request.user.is_recepcao):
		messages.error(request, 'Esta reserva não pode ser cancelada.')
		return redirect('reserva_detalhe', pk=pk)

	if request.method == 'POST':
		reserva.estado = 'cancelada'
		reserva.save()
		cancelado_pelo_cliente = not (request.user.is_admin or request.user.is_recepcao)
		if enviar_email_cancelamento_reserva(reserva, cancelado_pelo_cliente=cancelado_pelo_cliente):
			messages.success(request, 'Reserva cancelada com sucesso. O cliente foi notificado por email.')
		else:
			messages.success(request, 'Reserva cancelada com sucesso. (Erro ao enviar email ao cliente)')
		return redirect('reservas_lista')

	return render(request, 'reservas/cancelar.html', {'reserva': reserva})


@recepcao_funcionario_required
def reserva_editar(request, pk):
	"""Editar reserva (funcionário/admin)"""
	reserva = get_object_or_404(Reserva, pk=pk)
	valores_anteriores = {
		'cliente': reserva.cliente,
		'servico': reserva.servico,
		'funcionario': reserva.funcionario,
		'data': reserva.data,
		'hora': reserva.hora,
		'estado': reserva.estado,
		'notas': reserva.notas,
		'notas_internas': reserva.notas_internas,
		'preco_final': reserva.preco_final,
	}

	if request.method == 'POST':
		form = ReservaAdminForm(request.POST, instance=reserva)
		if form.is_valid():
			nova_reserva = form.save(commit=False)
			alteracoes = []

			for campo, valor_antigo in valores_anteriores.items():
				valor_novo = getattr(nova_reserva, campo)
				if valor_novo != valor_antigo:
					alteracoes.append({
						'campo': campo,
						'rotulo': form.fields[campo].label if campo in form.fields else campo,
						'antigo': valor_antigo,
						'novo': valor_novo,
					})

			if request.user.is_admin and request.POST.get('confirmar_conflitos') != '1':
				if (
					nova_reserva.data != reserva.data or
					nova_reserva.hora != reserva.hora or
					nova_reserva.funcionario != reserva.funcionario
				):
					conflito = Reserva.objects.filter(
						funcionario=nova_reserva.funcionario,
						data=nova_reserva.data,
						hora=nova_reserva.hora,
						estado__in=['pendente', 'confirmada']
					).exclude(pk=reserva.pk).first()

					if conflito:
						return render(request, 'reservas/editar.html', {
							'form': form,
							'reserva': reserva,
							'requires_confirmation': True,
							'conflito_reserva': conflito,
						})

			form.save()
			if alteracoes:
				if enviar_email_alteracao_reserva(reserva, alteracoes):
					messages.success(request, 'Reserva atualizada com sucesso! O cliente foi notificado por email.')
				else:
					messages.success(request, 'Reserva atualizada com sucesso! (Erro ao enviar email ao cliente)')
			else:
				messages.success(request, 'Reserva atualizada com sucesso!')
			return redirect('reserva_detalhe', pk=pk)
	else:
		form = ReservaAdminForm(instance=reserva)

	return render(request, 'reservas/editar.html', {'form': form, 'reserva': reserva})


def enviar_email_confirmacao_reserva(reserva):
	"""Enviar email de confirmação de reserva ao cliente"""
	try:
		contexto = {
			'cliente': reserva.cliente,
			'servico': reserva.servico,
			'data': reserva.data,
			'hora': reserva.hora,
			'funcionario': reserva.funcionario,
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/reserva_confirmada.html', contexto)
		text_message = render_to_string('emails/reserva_confirmada.txt', contexto)

		send_mail(
			subject=f'Reserva Confirmada - {reserva.servico.nome}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[reserva.cliente.email],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de confirmação enviado para {reserva.cliente.email} (Reserva #{reserva.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de confirmação: {e}')
		return False


def enviar_email_cancelamento_reserva(reserva, cancelado_pelo_cliente=False):
	"""Enviar email ao cliente quando a reserva é cancelada"""
	try:
		contexto = {
			'cliente': reserva.cliente,
			'servico': reserva.servico,
			'data': reserva.data,
			'hora': reserva.hora,
			'funcionario': reserva.funcionario,
			'cancelado_pelo_cliente': cancelado_pelo_cliente,
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/reserva_cancelada.html', contexto)
		text_message = render_to_string('emails/reserva_cancelada.txt', contexto)

		send_mail(
			subject=f'Reserva Cancelada - {reserva.servico.nome}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[reserva.cliente.email],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de cancelamento enviado para {reserva.cliente.email} (Reserva #{reserva.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de cancelamento: {e}')
		return False


def _formatar_valor_alteracao(valor):
	"""Formatar valores para exibição no email de alteração."""
	if valor is None:
		return 'vazio'
	if hasattr(valor, 'strftime'):
		if hasattr(valor, 'hour') and hasattr(valor, 'minute'):
			return valor.strftime('%H:%M')
		return valor.strftime('%d/%m/%Y')
	if hasattr(valor, 'get_full_name'):
		return valor.get_full_name() or valor.username
	return str(valor)


def enviar_email_alteracao_reserva(reserva, alteracoes):
	"""Enviar email ao cliente quando a reserva é alterada"""
	try:
		alteracoes_formatadas = [
			{
				'rotulo': alteracao['rotulo'],
				'antigo': _formatar_valor_alteracao(alteracao['antigo']),
				'novo': _formatar_valor_alteracao(alteracao['novo']),
			}
			for alteracao in alteracoes
		]

		contexto = {
			'cliente': reserva.cliente,
			'servico': reserva.servico,
			'data': reserva.data,
			'hora': reserva.hora,
			'funcionario': reserva.funcionario,
			'alteracoes': alteracoes_formatadas,
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/reserva_alterada.html', contexto)
		text_message = render_to_string('emails/reserva_alterada.txt', contexto)

		send_mail(
			subject=f'Reserva Atualizada - {reserva.servico.nome}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[reserva.cliente.email],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de alteração enviado para {reserva.cliente.email} (Reserva #{reserva.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de alteração de reserva: {e}')
		return False


@recepcao_funcionario_required
def reserva_confirmar(request, pk):
	"""Confirmar reserva"""
	reserva = get_object_or_404(Reserva, pk=pk)

	if reserva.estado == 'pendente':
		reserva.estado = 'confirmada'
		reserva.save()

		if enviar_email_confirmacao_reserva(reserva):
			messages.success(request, 'Reserva confirmada com sucesso! Email enviado ao cliente.')
		else:
			messages.success(request, 'Reserva confirmada com sucesso! (Erro ao enviar email)')

	return redirect('reserva_detalhe', pk=pk)


@recepcao_funcionario_required
def reserva_concluir(request, pk):
	"""Marcar reserva como concluída"""
	reserva = get_object_or_404(Reserva, pk=pk)

	if reserva.estado == 'confirmada':
		reserva.estado = 'concluida'
		reserva.save()
		if enviar_email_conclusao_reserva(reserva):
			messages.success(request, 'Reserva marcada como concluída! O cliente foi notificado por email.')
		else:
			messages.success(request, 'Reserva marcada como concluída! (Erro ao enviar email ao cliente)')

	return redirect('reserva_detalhe', pk=pk)


@recepcao_funcionario_required
def reserva_nao_compareceu(request, pk):
	"""Marcar reserva como não compareceu"""
	reserva = get_object_or_404(Reserva, pk=pk)

	if reserva.estado == 'confirmada':
		reserva.estado = 'nao_compareceu'
		reserva.save()

		if enviar_email_nao_compareceu_reserva(reserva):
			messages.success(request, 'Reserva marcada como não compareceu! O cliente foi notificado por email.')
		else:
			messages.success(request, 'Reserva marcada como não compareceu! (Erro ao enviar email ao cliente)')

	return redirect('reserva_detalhe', pk=pk)


def enviar_email_conclusao_reserva(reserva):
	"""Enviar email ao cliente quando a reserva é concluída"""
	try:
		contexto = {
			'cliente': reserva.cliente,
			'servico': reserva.servico,
			'data': reserva.data,
			'hora': reserva.hora,
			'funcionario': reserva.funcionario,
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/reserva_concluida.html', contexto)
		text_message = render_to_string('emails/reserva_concluida.txt', contexto)

		send_mail(
			subject=f'Reserva Concluída - {reserva.servico.nome}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[reserva.cliente.email],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de conclusão enviado para {reserva.cliente.email} (Reserva #{reserva.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de conclusão: {e}')
		return False


def enviar_email_nao_compareceu_reserva(reserva):
	"""Enviar email ao cliente quando a reserva é marcada como não compareceu"""
	try:
		contexto = {
			'cliente': reserva.cliente,
			'servico': reserva.servico,
			'data': reserva.data,
			'hora': reserva.hora,
			'funcionario': reserva.funcionario,
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/reserva_nao_compareceu.html', contexto)
		text_message = render_to_string('emails/reserva_nao_compareceu.txt', contexto)

		send_mail(
			subject=f'Reserva - Não Compareceu - {reserva.servico.nome}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[reserva.cliente.email],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de não compareceu enviado para {reserva.cliente.email} (Reserva #{reserva.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de não compareceu: {e}')
		return False
