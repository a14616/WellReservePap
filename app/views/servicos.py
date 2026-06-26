"""Vistas de serviços e categorias."""
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from itertools import zip_longest

from .auth import admin_required
from ..content_assets import servico_assets
from ..forms import CategoriaServicoForm, ServicoForm
from ..models import CategoriaServico, Servico, HorarioFuncionario, Utilizador


def _sync_service_horarios(servico, request):
	"""Create, update and delete horarios tied to a service from the submitted form rows."""
	existing_qs = HorarioFuncionario.objects.filter(servico=servico)
	existing_by_id = {str(h.pk): h for h in existing_qs}
	kept_ids = set()

	row_ids = request.POST.getlist('horario_id')
	funcionarios = request.POST.getlist('horario_funcionario')
	dias = request.POST.getlist('horario_dia_semana')
	horas_inicio = request.POST.getlist('horario_hora_inicio')
	horas_fim = request.POST.getlist('horario_hora_fim')
	datas_inicio = request.POST.getlist('horario_data_inicio')
	datas_fim = request.POST.getlist('horario_data_fim')

	for row_id, funcionario_id, dia, hora_inicio, hora_fim, data_inicio, data_fim in zip_longest(
		row_ids, funcionarios, dias, horas_inicio, horas_fim, datas_inicio, datas_fim, fillvalue=''
	):
		if not funcionario_id or dia == '' or not hora_inicio or not hora_fim:
			continue

		try:
			funcionario = Utilizador.objects.get(pk=int(funcionario_id), tipo='funcionario')
		except Exception:
			continue

		payload = {
			'servico': servico,
			'funcionario': funcionario,
			'dia_semana': int(dia),
			'hora_inicio': hora_inicio,
			'hora_fim': hora_fim,
			'ativo': True,
			'estado': 'aprovado',
			'data_inicio': data_inicio or None,
			'data_fim': data_fim or None,
		}

		obj = existing_by_id.get(str(row_id)) if row_id else None
		if obj:
			for field, value in payload.items():
				setattr(obj, field, value)
			obj.save()
			kept_ids.add(obj.pk)
		else:
			obj = HorarioFuncionario.objects.create(**payload)
			kept_ids.add(obj.pk)

	# Eliminar apenas os horários associados a este serviço que foram removidos do formulário
	for horario in existing_qs:
		if horario.pk not in kept_ids:
			horario.delete()


def _enrich_services(servicos):
	for servico in servicos:
		assets = servico_assets(servico)
		servico.imagem_capa = servico.imagem.url if getattr(servico, 'imagem', None) else assets['cover']
		servico.galeria_imagens = assets['gallery']
	return servicos


def servicos_lista(request):
	"""Lista de serviços"""
	categoria_id = request.GET.get('categoria')

	servicos = Servico.objects.filter(ativo=True).select_related('categoria')

	if categoria_id:
		servicos = servicos.filter(categoria_id=categoria_id)

	categorias = CategoriaServico.objects.filter(ativo=True)
	servicos = _enrich_services(list(servicos))

	context = {
		'servicos': servicos,
		'categorias': categorias,
		'categoria_selecionada': int(categoria_id) if categoria_id else None,
	}
	return render(request, 'servicos/lista.html', context)


def servico_detalhe(request, pk):
	"""Detalhe de um serviço"""
	servico = get_object_or_404(Servico, pk=pk, ativo=True)
	servico = _enrich_services([servico])[0]
	servicos_relacionados = _enrich_services(list(Servico.objects.filter(
		categoria=servico.categoria,
		ativo=True
	).exclude(pk=pk)[:4]))

	context = {
		'servico': servico,
		'servicos_relacionados': servicos_relacionados,
	}
	return render(request, 'servicos/detalhe.html', context)


@admin_required
def servicos_gestao(request):
	"""Gestão de serviços (admin)"""
	servicos = Servico.objects.select_related('categoria').all()
	pesquisa = request.GET.get('q', '').strip()
	categoria_id = request.GET.get('categoria', '').strip()
	ativo = request.GET.get('ativo', '').strip()

	if pesquisa:
		servicos = servicos.filter(Q(nome__icontains=pesquisa) | Q(descricao__icontains=pesquisa))
	if categoria_id:
		servicos = servicos.filter(categoria_id=categoria_id)
	if ativo in ['0', '1']:
		servicos = servicos.filter(ativo=(ativo == '1'))

	servicos = servicos.order_by('categoria__nome', 'nome')
	categorias = CategoriaServico.objects.all()

	context = {
		'servicos': servicos,
		'categorias': categorias,
	}
	return render(request, 'gestao/servicos.html', context)


@admin_required
def servico_criar(request):
	"""Criar novo serviço"""
	if request.method == 'POST':
		form = ServicoForm(request.POST, request.FILES)
		if form.is_valid():
			servico = form.save()
			if form.cleaned_data.get('criar_horario_fixo'):
				try:
					_sync_service_horarios(servico, request)
				except Exception:
					messages.warning(request, 'Serviço criado, mas não foi possível criar todos os horários fixos.')
			messages.success(request, 'Serviço criado com sucesso!')
			return redirect('servicos_gestao')
	else:
		form = ServicoForm()

	horarios_existentes = []
	return render(request, 'gestao/servico_form.html', {'form': form, 'titulo': 'Criar Serviço', 'horarios_existentes': horarios_existentes})


@admin_required
def servico_editar(request, pk):
	"""Editar serviço"""
	servico = get_object_or_404(Servico, pk=pk)

	if request.method == 'POST':
		form = ServicoForm(request.POST, request.FILES, instance=servico)
		if form.is_valid():
			servico = form.save()

			if form.cleaned_data.get('criar_horario_fixo'):
				try:
					_sync_service_horarios(servico, request)
				except Exception:
					messages.warning(request, 'Serviço atualizado, mas não foi possível criar todos os horários fixos.')
			messages.success(request, 'Serviço atualizado com sucesso!')
			return redirect('servicos_gestao')
	else:
		form = ServicoForm(instance=servico)

	# Pré-popular horários existentes para este serviço
	horarios_existentes = []
	try:
		horarios_qs = HorarioFuncionario.objects.filter(servico=servico)
		for h in horarios_qs:
			horarios_existentes.append({
				'id': h.pk,
				'funcionario_id': h.funcionario.pk,
				'dia_semana': h.dia_semana,
				'hora_inicio': h.hora_inicio.strftime('%H:%M'),
				'hora_fim': h.hora_fim.strftime('%H:%M'),
				'data_inicio': h.data_inicio.strftime('%Y-%m-%d') if h.data_inicio else '',
				'data_fim': h.data_fim.strftime('%Y-%m-%d') if h.data_fim else ''
			})
	except Exception:
		horarios_existentes = []

	return render(request, 'gestao/servico_form.html', {'form': form, 'titulo': 'Editar Serviço', 'servico': servico, 'horarios_existentes': horarios_existentes})


@admin_required
def servico_eliminar(request, pk):
	"""Eliminar serviço"""
	servico = get_object_or_404(Servico, pk=pk)

	if request.method == 'POST':
		servico.delete()
		messages.success(request, 'Serviço eliminado com sucesso!')
		return redirect('servicos_gestao')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': servico,
		'tipo': 'serviço',
		'voltar_url': 'servicos_gestao'
	})


@admin_required
def categorias_servicos_gestao(request):
	"""Gestão de categorias de serviços"""
	categorias = CategoriaServico.objects.annotate(num_servicos=Count('servicos')).order_by('ordem', 'nome')

	return render(request, 'gestao/categorias_servicos.html', {'categorias': categorias})


@admin_required
def categoria_servico_criar(request):
	"""Criar categoria de serviço"""
	if request.method == 'POST':
		form = CategoriaServicoForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Categoria criada com sucesso!')
			return redirect('categorias_servicos_gestao')
	else:
		form = CategoriaServicoForm()

	return render(request, 'gestao/categoria_form.html', {'form': form, 'titulo': 'Criar Categoria de Serviço'})


@admin_required
def categoria_servico_editar(request, pk):
	"""Editar categoria de serviço"""
	categoria = get_object_or_404(CategoriaServico, pk=pk)

	if request.method == 'POST':
		form = CategoriaServicoForm(request.POST, instance=categoria)
		if form.is_valid():
			form.save()
			messages.success(request, 'Categoria atualizada com sucesso!')
			return redirect('categorias_servicos_gestao')
	else:
		form = CategoriaServicoForm(instance=categoria)

	return render(request, 'gestao/categoria_form.html', {'form': form, 'titulo': 'Editar Categoria', 'categoria': categoria})


@admin_required
def bloqueios_gestao(request):
	from ..models import BloqueioHorario
	bloqueios = BloqueioHorario.objects.all().order_by('-data')
	return render(request, 'gestao/bloqueios.html', {'bloqueios': bloqueios})


@admin_required
def bloqueio_criar(request):
	from ..models import BloqueioHorario, Servico
	from ..models import Utilizador as UserModel

	servicos = Servico.objects.filter(ativo=True)
	funcionarios = UserModel.objects.filter(tipo='funcionario', is_active=True)

	if request.method == 'POST':
		servico_id = request.POST.get('servico') or None
		func_id = request.POST.get('funcionario') or None
		data = request.POST.get('data')
		hora_inicio = request.POST.get('hora_inicio')
		hora_fim = request.POST.get('hora_fim')
		motivo = request.POST.get('motivo', '')
		serv = Servico.objects.get(pk=servico_id) if servico_id else None
		func = UserModel.objects.get(pk=func_id) if func_id else None
		BloqueioHorario.objects.create(
			servico=serv,
			funcionario=func,
			data=data,
			hora_inicio=hora_inicio,
			hora_fim=hora_fim,
			motivo=motivo
		)
		messages.success(request, 'Bloqueio criado com sucesso.')
		return redirect('bloqueios_gestao')

	return render(request, 'gestao/bloqueio_form.html', {'servicos': servicos, 'funcionarios': funcionarios})


@admin_required
def bloqueio_eliminar(request, pk):
	from ..models import BloqueioHorario
	bloqueio = get_object_or_404(BloqueioHorario, pk=pk)
	if request.method == 'POST':
		bloqueio.delete()
		messages.success(request, 'Bloqueio removido.')
		return redirect('bloqueios_gestao')
	return redirect('bloqueios_gestao')


@admin_required
def categoria_servico_eliminar(request, pk):
	"""Eliminar categoria de serviço"""
	categoria = get_object_or_404(CategoriaServico, pk=pk)

	if request.method == 'POST':
		categoria.delete()
		messages.success(request, 'Categoria eliminada com sucesso!')
		return redirect('categorias_servicos_gestao')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': categoria,
		'tipo': 'categoria',
		'voltar_url': 'categorias_servicos_gestao'
	})
