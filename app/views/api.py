"""Vistas de API e PWA."""
import json
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import HttpResponse, JsonResponse

from ..models import FeriasFuncionario, HorarioFuncionario, Reserva, Servico, Utilizador


def pwa_manifest(request):
	"""Manifesto da PWA."""
	manifest = {
		"name": "WellReserve",
		"short_name": "WellReserve",
		"start_url": "/",
		"scope": "/",
		"display": "standalone",
		"background_color": "#f8f9fa",
		"theme_color": "#1a5f7a",
		"description": "Gestão de reservas, serviços e encomendas da WellReserve.",
		"icons": [
			{"src": "/static/img/logo-64.png", "sizes": "64x64", "type": "image/png"},
			{"src": "/static/img/logo-128.png", "sizes": "128x128", "type": "image/png"},
			{"src": "/static/img/logo-256.png", "sizes": "256x256", "type": "image/png"},
			{"src": "/static/img/logo-512.png", "sizes": "512x512", "type": "image/png"},
		],
	}
	response = HttpResponse(json.dumps(manifest), content_type='application/manifest+json')
	response['Cache-Control'] = 'no-cache'
	return response


def pwa_service_worker(request):
	"""Service worker simples para cache offline básico."""
	sw = """
const CACHE_NAME = 'wellreserve-v5';
const URLS_TO_CACHE = [
	'/',
	'/static/css/base.css',
	'/static/css/style.css',
	'/static/css/mobile.css',
	'/static/js/main.js',
	'/static/img/logo-64.png',
	'/static/img/logo-128.png',
	'/static/img/logo-256.png',
	'/static/img/logo-512.png'
];

self.addEventListener('install', event => {
	event.waitUntil(
		caches.open(CACHE_NAME).then(cache => cache.addAll(URLS_TO_CACHE))
	);
	self.skipWaiting();
});

self.addEventListener('activate', event => {
	event.waitUntil(
		caches.keys().then(keys => Promise.all(
			keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
		)).then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', event => {
	if (event.request.method !== 'GET') return;

	if (event.request.mode === 'navigate') {
		event.respondWith(
			fetch(event.request).catch(() => caches.match('/'))
		);
		return;
	}

	if (event.request.destination === 'style' || event.request.destination === 'script') {
		event.respondWith(
			fetch(event.request).then(networkResponse => {
				const clone = networkResponse.clone();
				caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
				return networkResponse;
			}).catch(() => caches.match(event.request))
		);
		return;
	}

	event.respondWith(
		caches.match(event.request).then(response => {
			return response || fetch(event.request).then(networkResponse => {
				return networkResponse;
			});
		})
	);
});
"""
	response = HttpResponse(sw, content_type='application/javascript')
	response['Cache-Control'] = 'no-cache'
	return response


def health_check(request):
	"""Resposta mínima para verificar se o processo responde no Railway."""
	return HttpResponse('ok', content_type='text/plain')


def api_horarios_disponiveis(request):
	"""API para obter horários disponíveis"""
	servico_id = request.GET.get('servico')
	data_str = request.GET.get('data')
	funcionario_id = request.GET.get('funcionario')

	if not servico_id or not data_str:
		return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)

	try:
		servico = Servico.objects.get(pk=servico_id, ativo=True)
		data = datetime.strptime(data_str, '%Y-%m-%d').date()
	except (Servico.DoesNotExist, ValueError):
		return JsonResponse({'error': 'Serviço ou data inválidos'}, status=400)

	dia_semana = data.weekday()

	horarios_disponiveis = []
	seen = set()
	from ..models import BloqueioHorario

	horarios_servico = HorarioFuncionario.objects.filter(
		servico=servico,
		dia_semana=dia_semana,
		ativo=True,
		estado='aprovado'
	)

	if horarios_servico.exists():
		if funcionario_id:
			horarios_servico = horarios_servico.filter(funcionario_id=funcionario_id)

		for horario in horarios_servico:
			funcionario = horario.funcionario
			if horario.data_inicio and data < horario.data_inicio:
				continue
			if horario.data_fim and data > horario.data_fim:
				continue

			em_ferias = FeriasFuncionario.objects.filter(
				funcionario=funcionario,
				data_inicio__lte=data,
				data_fim__gte=data,
				estado='aprovado'
			).exists()
			if em_ferias:
				continue

			hora_atual = datetime.combine(data, horario.hora_inicio)
			hora_fim = datetime.combine(data, horario.hora_fim)

			while hora_atual + timedelta(minutes=servico.duracao) <= hora_fim:
				reserva_existente = Reserva.objects.filter(
					funcionario=funcionario,
					data=data,
					hora=hora_atual.time(),
					estado__in=['pendente', 'confirmada']
				).exists()

				bloqueio = BloqueioHorario.objects.filter(
					Q(funcionario=funcionario, data=data, hora_inicio__lte=hora_atual.time(), hora_fim__gt=hora_atual.time()) |
					Q(servico=servico, data=data, hora_inicio__lte=hora_atual.time(), hora_fim__gt=hora_atual.time())
				).exists()

				key = (hora_atual.strftime('%H:%M'), funcionario.pk)
				if not reserva_existente and not bloqueio and key not in seen:
					horarios_disponiveis.append({
						'hora': hora_atual.strftime('%H:%M'),
						'funcionario_id': funcionario.pk,
						'funcionario_nome': funcionario.get_full_name()
					})
					seen.add(key)

				hora_atual += timedelta(minutes=30)
	else:
		if funcionario_id:
			funcionarios = Utilizador.objects.filter(pk=funcionario_id, tipo='funcionario')
		else:
			funcionarios = servico.funcionarios.filter(is_active=True)

		for funcionario in funcionarios:
			em_ferias = FeriasFuncionario.objects.filter(
				funcionario=funcionario,
				data_inicio__lte=data,
				data_fim__gte=data,
				estado='aprovado'
			).exists()
			if em_ferias:
				continue

			horarios = HorarioFuncionario.objects.filter(
				funcionario=funcionario,
				servico__isnull=True,
				dia_semana=dia_semana,
				ativo=True,
				estado='aprovado'
			)

			for horario in horarios:
				if horario.data_inicio and data < horario.data_inicio:
					continue
				if horario.data_fim and data > horario.data_fim:
					continue

				hora_atual = datetime.combine(data, horario.hora_inicio)
				hora_fim = datetime.combine(data, horario.hora_fim)
				while hora_atual + timedelta(minutes=servico.duracao) <= hora_fim:
					reserva_existente = Reserva.objects.filter(
						funcionario=funcionario,
						data=data,
						hora=hora_atual.time(),
						estado__in=['pendente', 'confirmada']
					).exists()

					bloqueio = BloqueioHorario.objects.filter(
						Q(funcionario=funcionario, data=data, hora_inicio__lte=hora_atual.time(), hora_fim__gt=hora_atual.time()) |
						Q(servico=servico, data=data, hora_inicio__lte=hora_atual.time(), hora_fim__gt=hora_atual.time())
					).exists()

					key = (hora_atual.strftime('%H:%M'), funcionario.pk)
					if not reserva_existente and not bloqueio and key not in seen:
						horarios_disponiveis.append({
							'hora': hora_atual.strftime('%H:%M'),
							'funcionario_id': funcionario.pk,
							'funcionario_nome': funcionario.get_full_name()
						})
						seen.add(key)

					hora_atual += timedelta(minutes=30)

	horarios_disponiveis.sort(key=lambda x: x['hora'])
	return JsonResponse({'horarios': horarios_disponiveis})


def api_procurar_clientes(request):
	"""API para procurar clientes por email, username ou telefone"""
	query = request.GET.get('q', '').strip()

	if not query or len(query) < 2:
		return JsonResponse({'clientes': []})

	clientes = Utilizador.objects.filter(
		tipo='cliente',
		is_active=True
	).filter(
		Q(email__icontains=query) |
		Q(username__icontains=query) |
		Q(telefone__icontains=query) |
		Q(first_name__icontains=query) |
		Q(last_name__icontains=query)
	)[:20]

	resultado = []
	for cliente in clientes:
		resultado.append({
			'id': cliente.pk,
			'nome': cliente.get_full_name() or cliente.username,
			'email': cliente.email,
			'telefone': cliente.telefone or '-',
			'username': cliente.username,
		})

	return JsonResponse({'clientes': resultado})
