"""Vistas de autenticação."""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from ..forms import LoginForm, RegistoForm
from ..models import Utilizador


def admin_required(view_func):
	"""Decorador para verificar se o utilizador é administrador"""
	def wrapper(request, *args, **kwargs):
		if not request.user.is_authenticated:
			messages.error(request, 'Precisa de fazer login para aceder a esta página.')
			return redirect('login')
		if not request.user.is_admin:
			messages.error(request, 'Não tem permissão para aceder a esta página.')
			return redirect('dashboard')
		return view_func(request, *args, **kwargs)
	return wrapper


def funcionario_required(view_func):
	"""Decorador para verificar se o utilizador é funcionário ou admin"""
	def wrapper(request, *args, **kwargs):
		if not request.user.is_authenticated:
			messages.error(request, 'Precisa de fazer login para aceder a esta página.')
			return redirect('login')
		if not (request.user.is_admin or request.user.is_funcionario):
			messages.error(request, 'Não tem permissão para aceder a esta página.')
			return redirect('dashboard')
		return view_func(request, *args, **kwargs)
	return wrapper


def recepcao_funcionario_required(view_func):
	"""Decorador para verificar se o utilizador é receção, funcionário ou admin"""
	def wrapper(request, *args, **kwargs):
		if not request.user.is_authenticated:
			messages.error(request, 'Precisa de fazer login para aceder a esta página.')
			return redirect('login')
		if not (request.user.is_admin or request.user.is_recepcao or request.user.is_funcionario):
			messages.error(request, 'Não tem permissão para aceder a esta página.')
			return redirect('dashboard')
		return view_func(request, *args, **kwargs)
	return wrapper


def enviar_email_boas_vindas(utilizador):
	"""Enviar email de boas-vindas ao novo utilizador"""
	try:
		tipo_display = dict(Utilizador.TIPO_CHOICES).get(utilizador.tipo, utilizador.tipo)

		contexto = {
			'usuario': utilizador,
			'tipo_utilizador_display': tipo_display,
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/conta_criada.html', contexto)
		text_message = render_to_string('emails/conta_criada.txt', contexto)

		send_mail(
			subject='Bem-vindo(a) a WellReserve!',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[utilizador.email],
			html_message=html_message,
			fail_silently=False,
		)
		return True
	except Exception:
		return False


def registo(request):
	"""Registo de novos utilizadores"""
	if request.user.is_authenticated:
		return redirect('dashboard')

	if request.method == 'POST':
		form = RegistoForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)

			if enviar_email_boas_vindas(user):
				messages.success(request, f'Bem-vindo(a), {user.first_name}! A sua conta foi criada com sucesso. Verifique o seu email para confirmar.')
			else:
				messages.success(request, f'Bem-vindo(a), {user.first_name}! A sua conta foi criada com sucesso.')

			return redirect('dashboard')
	else:
		form = RegistoForm()

	return render(request, 'auth/registo.html', {'form': form})


def login_view(request):
	"""Login de utilizadores"""
	if request.user.is_authenticated:
		return redirect('dashboard')

	if request.method == 'POST':
		form = LoginForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			messages.success(request, f'Bem-vindo(a) de volta, {user.first_name}!')
			next_url = request.GET.get('next', 'dashboard')
			return redirect(next_url)
	else:
		form = LoginForm()

	return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
	"""Logout de utilizadores"""
	logout(request)
	messages.info(request, 'Sessão terminada com sucesso.')
	return redirect('home')
