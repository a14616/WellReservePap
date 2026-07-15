"""Vistas públicas e do dashboard."""
import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from ..forms import ContactoForm, PerfilForm
from ..content_assets import produto_assets, servico_assets
from ..models import CategoriaServico, Contacto, Encomenda, Produto, Reserva, Servico, HorarioFuncionario, Utilizador

logger = logging.getLogger(__name__)


def _enrich_products(produtos):
	for produto in produtos:
		assets = produto_assets(produto)
		produto.imagem_capa = produto.imagem.url if getattr(produto, 'imagem', None) else assets['cover']
		produto.galeria_imagens = assets['gallery']
	return produtos


def _enrich_services(servicos):
	for servico in servicos:
		assets = servico_assets(servico)
		servico.imagem_capa = servico.imagem.url if getattr(servico, 'imagem', None) else assets['cover']
		servico.galeria_imagens = assets['gallery']
	return servicos


def home(request):
	"""Página inicial"""
	try:
		servicos_destaque = _enrich_services(list(Servico.objects.filter(ativo=True, destaque=True)[:6]))
		produtos_destaque = _enrich_products(list(Produto.objects.filter(ativo=True, destaque=True)[:6]))
		categorias = CategoriaServico.objects.filter(ativo=True)
	except Exception:
		logger.exception("Erro ao carregar dados da home page")
		servicos_destaque = []
		produtos_destaque = []
		categorias = []

	context = {
		'servicos_destaque': servicos_destaque,
		'produtos_destaque': produtos_destaque,
		'categorias': categorias,
	}
	return render(request, 'home.html', context)


def sobre(request):
	"""Página sobre nós"""
	return render(request, 'sobre.html')


def contacto(request):
	"""Página de contacto"""
	if request.method == 'POST':
		form = ContactoForm(request.POST)
		if form.is_valid():
			contacto_obj = form.save()
			assunto_email = f"[WellReserve] {contacto_obj.assunto}"
			corpo_email = (
				f"Nome: {contacto_obj.nome}\n"
				f"Email: {contacto_obj.email}\n"
				f"Telefone: {contacto_obj.telefone or '-'}\n\n"
				f"Mensagem:\n{contacto_obj.mensagem}"
			)
			try:
				send_mail(
					assunto_email,
					corpo_email,
					settings.DEFAULT_FROM_EMAIL,
					[settings.CONTACTO_EMAIL_DESTINO],
					fail_silently=True,
				)
			except Exception:
				pass

			messages.success(request, 'Mensagem enviada com sucesso! Entraremos em contacto brevemente.')
			return redirect('contacto')
	else:
		form = ContactoForm()

	return render(request, 'contacto.html', {'form': form})


@login_required
def dashboard(request):
	"""Dashboard principal - redireciona conforme o tipo de utilizador"""
	if request.user.is_admin:
		return dashboard_admin(request)
	elif request.user.is_recepcao:
		return dashboard_recepcao(request)
	elif request.user.is_funcionario:
		return dashboard_funcionario(request)
	else:
		return dashboard_cliente(request)


def dashboard_admin(request):
	"""Dashboard do administrador"""
	hoje = date.today()

	total_clientes = Utilizador.objects.filter(tipo='cliente').count()
	total_funcionarios = Utilizador.objects.filter(tipo='funcionario').count()
	reservas_hoje = Reserva.objects.filter(data=hoje).count()
	reservas_pendentes = Reserva.objects.filter(estado='pendente').count()
	encomendas_pendentes = Encomenda.objects.filter(estado__in=['pendente', 'preparacao']).count()

	reservas_recentes = Reserva.objects.select_related('cliente', 'servico').order_by('-data_criacao')[:10]
	encomendas_recentes = Encomenda.objects.select_related('cliente').order_by('-data_criacao')[:5]
	contactos_nao_lidos = Contacto.objects.filter(lida=False).count()

	context = {
		'total_clientes': total_clientes,
		'total_funcionarios': total_funcionarios,
		'reservas_hoje': reservas_hoje,
		'reservas_pendentes': reservas_pendentes,
		'encomendas_pendentes': encomendas_pendentes,
		'reservas_recentes': reservas_recentes,
		'encomendas_recentes': encomendas_recentes,
		'contactos_nao_lidos': contactos_nao_lidos,
	}
	return render(request, 'dashboard/admin.html', context)


def dashboard_funcionario(request):
	"""Dashboard do funcionário"""
	hoje = date.today()

	minhas_reservas_hoje = Reserva.objects.filter(funcionario=request.user, data=hoje).select_related('cliente', 'servico').order_by('hora')
	proximas_reservas = Reserva.objects.filter(funcionario=request.user, data__gte=hoje, estado__in=['pendente', 'confirmada']).select_related('cliente', 'servico').order_by('data', 'hora')[:10]
	meus_horarios = HorarioFuncionario.objects.filter(funcionario=request.user, ativo=True, estado='aprovado').order_by('dia_semana', 'hora_inicio')
	minhas_reservas = Reserva.objects.filter(cliente=request.user).select_related('servico', 'funcionario').order_by('-data', '-hora')[:10]
	proximas_reservas_cliente = Reserva.objects.filter(cliente=request.user, data__gte=hoje, estado__in=['pendente', 'confirmada']).select_related('servico', 'funcionario').order_by('data', 'hora')[:5]

	context = {
		'minhas_reservas_hoje': minhas_reservas_hoje,
		'proximas_reservas': proximas_reservas,
		'meus_horarios': meus_horarios,
		'minhas_reservas': minhas_reservas,
		'proximas_reservas_cliente': proximas_reservas_cliente,
	}
	return render(request, 'dashboard/funcionario.html', context)


def dashboard_recepcao(request):
	"""Dashboard da receção"""
	hoje = date.today()

	todas_reservas = Reserva.objects.select_related('cliente', 'servico', 'funcionario').order_by('-data', '-hora')[:20]
	reservas_pendentes_hoje = Reserva.objects.filter(data=hoje, estado='pendente').select_related('cliente', 'servico').order_by('hora')
	proximas_reservas = Reserva.objects.filter(data__gte=hoje, estado__in=['pendente', 'confirmada']).select_related('cliente', 'servico', 'funcionario').order_by('data', 'hora')[:15]
	todos_horarios = HorarioFuncionario.objects.filter(ativo=True, estado='aprovado').select_related('funcionario').order_by('dia_semana', 'hora_inicio')

	context = {
		'todas_reservas': todas_reservas,
		'reservas_pendentes_hoje': reservas_pendentes_hoje,
		'proximas_reservas': proximas_reservas,
		'todos_horarios': todos_horarios,
	}
	return render(request, 'dashboard/recepcao.html', context)


def dashboard_cliente(request):
	"""Dashboard do cliente"""
	hoje = date.today()

	minhas_reservas = Reserva.objects.filter(cliente=request.user).select_related('servico', 'funcionario').order_by('-data', '-hora')[:10]
	proximas_reservas = Reserva.objects.filter(cliente=request.user, data__gte=hoje, estado__in=['pendente', 'confirmada']).select_related('servico', 'funcionario').order_by('data', 'hora')[:5]
	minhas_encomendas = Encomenda.objects.filter(cliente=request.user).order_by('-data_criacao')[:5]
	servicos_destaque = Servico.objects.filter(ativo=True, destaque=True)[:4]
	total_reservas = Reserva.objects.filter(cliente=request.user).count()
	total_encomendas = Encomenda.objects.filter(cliente=request.user).count()
	reservas_futuras = Reserva.objects.filter(cliente=request.user, data__gte=hoje, estado__in=['pendente', 'confirmada']).count()

	context = {
		'minhas_reservas': minhas_reservas,
		'proximas_reservas': proximas_reservas,
		'minhas_encomendas': minhas_encomendas,
		'servicos_destaque': servicos_destaque,
		'total_reservas': total_reservas,
		'total_encomendas': total_encomendas,
		'reservas_futuras': reservas_futuras,
	}
	return render(request, 'dashboard/cliente.html', context)


@login_required
def perfil(request):
	"""Ver e editar perfil"""
	if request.method == 'POST':
		form = PerfilForm(request.POST, request.FILES, instance=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Perfil atualizado com sucesso!')
			return redirect('perfil')
	else:
		form = PerfilForm(instance=request.user)

	return render(request, 'perfil.html', {'form': form})


@login_required
def alterar_password(request):
	"""Alterar a palavra-passe do utilizador"""
	if request.method == 'POST':
		password_atual = request.POST.get('password_atual')
		password_nova = request.POST.get('password_nova')
		password_confirmar = request.POST.get('password_confirmar')

		if not request.user.check_password(password_atual):
			messages.error(request, 'Palavra-passe atual incorreta!')
			return redirect('perfil')

		if password_nova != password_confirmar:
			messages.error(request, 'As novas palavras-passe não coincidem!')
			return redirect('perfil')

		if len(password_nova) < 8:
			messages.error(request, 'A nova palavra-passe deve ter pelo menos 8 caracteres!')
			return redirect('perfil')

		request.user.set_password(password_nova)
		request.user.save()
		update_session_auth_hash(request, request.user)

		messages.success(request, 'Palavra-passe alterada com sucesso!')
		return redirect('perfil')

	return redirect('perfil')
