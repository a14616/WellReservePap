"""Vistas de gestão de utilizadores, horários, férias e relatórios."""
from datetime import date, datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .auth import admin_required, recepcao_funcionario_required
from ..forms import FeriasFuncionarioForm, HorarioFuncionarioForm, UtilizadorAdminForm
from ..models import CategoriaServico, Encomenda, FeriasFuncionario, HorarioFuncionario, Reserva, Servico, Utilizador


@admin_required
def utilizadores_lista(request):
	"""Lista de utilizadores"""
	tipo = request.GET.get('tipo', '')
	pesquisa = request.GET.get('q', '')
	ativo = request.GET.get('ativo', '').strip()

	utilizadores = Utilizador.objects.all()

	if tipo:
		utilizadores = utilizadores.filter(tipo=tipo)

	if ativo in ['0', '1']:
		utilizadores = utilizadores.filter(is_active=(ativo == '1'))

	if pesquisa:
		utilizadores = utilizadores.filter(
			Q(username__icontains=pesquisa) |
			Q(first_name__icontains=pesquisa) |
			Q(last_name__icontains=pesquisa) |
			Q(email__icontains=pesquisa)
		)

	utilizadores = utilizadores.order_by('-date_joined')

	total_clientes = Utilizador.objects.filter(tipo='cliente').count()
	total_funcionarios = Utilizador.objects.filter(tipo='funcionario').count()
	total_admins = Utilizador.objects.filter(tipo='admin').count()

	paginator = Paginator(utilizadores, 20)
	page = request.GET.get('page')
	utilizadores = paginator.get_page(page)

	context = {
		'utilizadores': utilizadores,
		'tipo_selecionado': tipo,
		'pesquisa': pesquisa,
		'ativo_selecionado': ativo,
		'total_clientes': total_clientes,
		'total_funcionarios': total_funcionarios,
		'total_admins': total_admins,
	}
	return render(request, 'gestao/utilizadores.html', context)


@admin_required
def utilizador_detalhe(request, pk):
	"""Detalhe de um utilizador"""
	utilizador = get_object_or_404(Utilizador, pk=pk)
	reservas = Reserva.objects.filter(cliente=utilizador).select_related('servico').order_by('-data', '-hora')[:10]
	encomendas = Encomenda.objects.filter(cliente=utilizador).order_by('-data_criacao')[:10]

	context = {
		'utilizador': utilizador,
		'reservas': reservas,
		'encomendas': encomendas,
	}
	return render(request, 'gestao/utilizador_detalhe.html', context)


@admin_required
def utilizador_criar(request):
	"""Criar novo utilizador"""
	if request.method == 'POST':
		form = UtilizadorAdminForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			password = request.POST.get('password')
			if password:
				user.set_password(password)
			user.save()
			messages.success(request, 'Utilizador criado com sucesso!')
			return redirect('utilizadores_lista')
	else:
		form = UtilizadorAdminForm()

	return render(request, 'gestao/utilizador_form.html', {'form': form, 'titulo': 'Criar Utilizador'})


@admin_required
def utilizador_editar(request, pk):
	"""Editar utilizador"""
	utilizador = get_object_or_404(Utilizador, pk=pk)

	if request.method == 'POST':
		form = UtilizadorAdminForm(request.POST, instance=utilizador)
		if form.is_valid():
			form.save()
			messages.success(request, 'Utilizador atualizado com sucesso!')
			return redirect('utilizadores_lista')
	else:
		form = UtilizadorAdminForm(instance=utilizador)

	return render(request, 'gestao/utilizador_form.html', {'form': form, 'titulo': 'Editar Utilizador', 'utilizador': utilizador})


@admin_required
def utilizador_eliminar(request, pk):
	"""Eliminar utilizador"""
	utilizador = get_object_or_404(Utilizador, pk=pk)

	if utilizador == request.user:
		messages.error(request, 'Não pode eliminar a sua própria conta.')
		return redirect('utilizadores_lista')

	if request.method == 'POST':
		utilizador.delete()
		messages.success(request, 'Utilizador eliminado com sucesso!')
		return redirect('utilizadores_lista')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': utilizador,
		'tipo': 'utilizador',
		'voltar_url': 'utilizadores_lista'
	})


@recepcao_funcionario_required
def horarios_gestao(request):
	"""Gestão de horários"""
	if request.user.is_admin or request.user.is_recepcao:
		horarios = HorarioFuncionario.objects.select_related('funcionario').all()
		funcionarios = Utilizador.objects.filter(tipo__in=['funcionario', 'recepcao'], is_active=True)
		lista_ferias = FeriasFuncionario.objects.select_related('funcionario').all()
	else:
		horarios = HorarioFuncionario.objects.filter(funcionario=request.user)
		funcionarios = None
		lista_ferias = FeriasFuncionario.objects.filter(funcionario=request.user)

	horario_funcionario_id = request.GET.get('horario_funcionario', '').strip()
	ferias_funcionario_id = request.GET.get('ferias_funcionario', '').strip()
	ferias_data_inicio = request.GET.get('ferias_data_inicio', '').strip()
	ferias_data_fim = request.GET.get('ferias_data_fim', '').strip()

	if (request.user.is_admin or request.user.is_recepcao) and horario_funcionario_id:
		horarios = horarios.filter(funcionario_id=horario_funcionario_id)

	if (request.user.is_admin or request.user.is_recepcao) and ferias_funcionario_id:
		lista_ferias = lista_ferias.filter(funcionario_id=ferias_funcionario_id)

	if ferias_data_inicio:
		try:
			lista_ferias = lista_ferias.filter(data_inicio__gte=datetime.fromisoformat(ferias_data_inicio).date())
		except ValueError:
			pass

	if ferias_data_fim:
		try:
			lista_ferias = lista_ferias.filter(data_fim__lte=datetime.fromisoformat(ferias_data_fim).date())
		except ValueError:
			pass

	horarios = horarios.order_by('estado', 'funcionario', 'dia_semana', 'hora_inicio')
	lista_ferias = lista_ferias.order_by('estado', '-data_inicio')

	context = {
		'horarios': horarios,
		'funcionarios': funcionarios,
		'lista_ferias': lista_ferias,
	}
	return render(request, 'gestao/horarios.html', context)


def _reservas_em_conflito_horario(funcionario, dia_semana, hora_inicio, hora_fim):
	"""Retorna reservas futuras que caem dentro do período de horário definido."""
	reservas = Reserva.objects.filter(
		funcionario=funcionario,
		estado__in=['pendente', 'confirmada'],
		data__gte=date.today(),
	).select_related('cliente', 'servico').order_by('data', 'hora')

	conflitos = [
		reserva for reserva in reservas
		if reserva.data.weekday() == dia_semana and hora_inicio <= reserva.hora < hora_fim
	]
	return conflitos


@recepcao_funcionario_required
def horario_criar(request):
	"""Criar novo horário"""
	if request.method == 'POST':
		form = HorarioFuncionarioForm(request.POST, user=request.user)

		if form.is_valid():
			horario = form.save(commit=False)
			if not request.user.is_admin:
				horario.funcionario = request.user
				horario.estado = 'pendente'
				horario.ativo = False
			else:
				horario.estado = 'aprovado'
				horario.ativo = True

			if request.user.is_admin and request.POST.get('confirmar_conflitos') != '1':
				conflitos = _reservas_em_conflito_horario(
					funcionario=horario.funcionario,
					dia_semana=horario.dia_semana,
					hora_inicio=horario.hora_inicio,
					hora_fim=horario.hora_fim,
				)
				if conflitos:
					return render(request, 'gestao/horario_form.html', {
						'form': form,
						'titulo': 'Criar Horário',
						'requires_confirmation': True,
						'conflitos_reservas': conflitos[:10],
						'conflitos_total': len(conflitos),
					})

			horario.save()
			if request.user.is_admin:
				messages.success(request, 'Horário criado com sucesso!')
			else:
				messages.success(request, 'Pedido de horário enviado para aprovação.')
			return redirect('horarios_gestao')
	else:
		form = HorarioFuncionarioForm(user=request.user)

	return render(request, 'gestao/horario_form.html', {'form': form, 'titulo': 'Criar Horário'})


@recepcao_funcionario_required
def horario_editar(request, pk):
	"""Editar horário"""
	if request.user.is_admin:
		horario = get_object_or_404(HorarioFuncionario, pk=pk)
	else:
		horario = get_object_or_404(HorarioFuncionario, pk=pk, funcionario=request.user)

	if request.method == 'POST':
		form = HorarioFuncionarioForm(request.POST, instance=horario, user=request.user)

		if form.is_valid():
			novo_horario = form.save(commit=False)

			if not request.user.is_admin:
				novo_horario.funcionario = request.user
				novo_horario.estado = 'pendente'
				novo_horario.ativo = False

			if request.user.is_admin and request.POST.get('confirmar_conflitos') != '1':
				conflitos = _reservas_em_conflito_horario(
					funcionario=novo_horario.funcionario,
					dia_semana=novo_horario.dia_semana,
					hora_inicio=novo_horario.hora_inicio,
					hora_fim=novo_horario.hora_fim,
				)
				if conflitos:
					return render(request, 'gestao/horario_form.html', {
						'form': form,
						'titulo': 'Editar Horário',
						'horario': horario,
						'requires_confirmation': True,
						'conflitos_reservas': conflitos[:10],
						'conflitos_total': len(conflitos),
					})

			form.save()
			if request.user.is_admin:
				messages.success(request, 'Horário atualizado com sucesso!')
			else:
				messages.success(request, 'Pedido de horário atualizado e enviado para aprovação.')
			return redirect('horarios_gestao')
	else:
		form = HorarioFuncionarioForm(instance=horario, user=request.user)

	return render(request, 'gestao/horario_form.html', {'form': form, 'titulo': 'Editar Horário', 'horario': horario})


@admin_required
def horario_aprovar(request, pk):
	"""Aprovar pedido de horário"""
	horario = get_object_or_404(HorarioFuncionario, pk=pk)
	horario.estado = 'aprovado'
	horario.ativo = True
	horario.save(update_fields=['estado', 'ativo'])
	messages.success(request, 'Horário aprovado com sucesso!')
	return redirect('horarios_gestao')


@recepcao_funcionario_required
def horario_eliminar(request, pk):
	"""Eliminar horário"""
	if request.user.is_admin:
		horario = get_object_or_404(HorarioFuncionario, pk=pk)
	else:
		horario = get_object_or_404(HorarioFuncionario, pk=pk, funcionario=request.user)

	if request.method == 'POST':
		horario.delete()
		messages.success(request, 'Horário eliminado com sucesso!')
		return redirect('horarios_gestao')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': horario,
		'tipo': 'horário',
		'voltar_url': 'horarios_gestao'
	})


@recepcao_funcionario_required
def ferias_criar(request):
	"""Criar período de férias/ausência"""
	if request.method == 'POST':
		form = FeriasFuncionarioForm(request.POST, user=request.user)

		if form.is_valid():
			ferias = form.save(commit=False)
			if not request.user.is_admin:
				ferias.funcionario = request.user
				ferias.estado = 'pendente'
			else:
				ferias.estado = 'aprovado'
			ferias.save()
			if request.user.is_admin:
				messages.success(request, 'Período de férias/ausência criado com sucesso!')
			else:
				messages.success(request, 'Pedido de férias/ausência enviado para aprovação.')
			return redirect('horarios_gestao')
	else:
		form = FeriasFuncionarioForm(user=request.user)

	return render(request, 'gestao/ferias_form.html', {'form': form, 'titulo': 'Registar Férias/Ausência'})


@admin_required
def ferias_aprovar(request, pk):
	"""Aprovar pedido de férias/ausência"""
	ferias = get_object_or_404(FeriasFuncionario, pk=pk)
	ferias.estado = 'aprovado'
	ferias.save(update_fields=['estado'])
	messages.success(request, 'Pedido de férias/ausência aprovado com sucesso!')
	return redirect('horarios_gestao')


@recepcao_funcionario_required
def ferias_eliminar(request, pk):
	"""Eliminar período de férias/ausência"""
	if request.user.is_admin:
		ferias = get_object_or_404(FeriasFuncionario, pk=pk)
	else:
		ferias = get_object_or_404(FeriasFuncionario, pk=pk, funcionario=request.user)

	if request.method == 'POST':
		ferias.delete()
		messages.success(request, 'Período de férias/ausência eliminado com sucesso!')
		return redirect('horarios_gestao')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': ferias,
		'tipo': 'férias/ausência',
		'voltar_url': 'horarios_gestao'
	})


@admin_required
def relatorios(request):
	"""Página de relatórios"""
	hoje = date.today()
	inicio_mes = hoje.replace(day=1)

	reservas_mes = Reserva.objects.filter(data__gte=inicio_mes)
	total_reservas_mes = reservas_mes.count()
	reservas_concluidas_mes = reservas_mes.filter(estado='concluida').count()
	receita_mes = reservas_mes.filter(estado='concluida').aggregate(total=Sum('preco_final'))['total'] or 0

	encomendas_mes = Encomenda.objects.filter(data_criacao__gte=inicio_mes)
	total_encomendas_mes = encomendas_mes.count()
	receita_encomendas_mes = encomendas_mes.filter(estado='concluida').aggregate(total=Sum('total'))['total'] or 0

	servicos_populares = Servico.objects.annotate(
		num_reservas=Count('reservas', filter=Q(reservas__data__gte=inicio_mes))
	).order_by('-num_reservas')[:5]

	novos_clientes = Utilizador.objects.filter(
		tipo='cliente',
		date_joined__gte=inicio_mes
	).count()

	context = {
		'total_reservas_mes': total_reservas_mes,
		'reservas_concluidas_mes': reservas_concluidas_mes,
		'receita_mes': receita_mes,
		'total_encomendas_mes': total_encomendas_mes,
		'receita_encomendas_mes': receita_encomendas_mes,
		'servicos_populares': servicos_populares,
		'novos_clientes': novos_clientes,
	}
	return render(request, 'gestao/relatorios.html', context)
