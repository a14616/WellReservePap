"""Vistas de encomendas e faturas."""
from datetime import datetime
from decimal import Decimal
from io import BytesIO
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from xml.sax.saxutils import escape

from .auth import recepcao_funcionario_required
from ..forms import CheckoutEncomendaForm
from ..models import Encomenda, ItemEncomenda, Produto

logger = logging.getLogger(__name__)


def _import_reportlab():
	"""Import reportlab components lazily and raise clear error if missing."""
	try:
		from reportlab.lib import colors
		from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
		from reportlab.lib.pagesizes import A4
		from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
		from reportlab.lib.units import mm
		from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
		return {
			'colors': colors,
			'TA_LEFT': TA_LEFT,
			'TA_CENTER': TA_CENTER,
			'TA_RIGHT': TA_RIGHT,
			'A4': A4,
			'ParagraphStyle': ParagraphStyle,
			'getSampleStyleSheet': getSampleStyleSheet,
			'mm': mm,
			'Paragraph': Paragraph,
			'SimpleDocTemplate': SimpleDocTemplate,
			'Spacer': Spacer,
			'Table': Table,
			'TableStyle': TableStyle,
		}
	except ImportError as e:
		raise ImportError('reportlab is required to generate PDFs. Install it with `pip install reportlab`.') from e


def _garantir_numero_fatura(encomenda):
	"""Garantir que a encomenda tem número de fatura."""
	if not encomenda.numero_fatura:
		data_base = timezone.localtime(encomenda.data_criacao) if encomenda.data_criacao else timezone.localtime()
		encomenda.numero_fatura = f'FAT-{data_base.strftime("%Y%m%d")}-{encomenda.pk:05d}'
		encomenda.save(update_fields=['numero_fatura'])

	return encomenda.numero_fatura


def _contexto_fatura_encomenda(encomenda):
	"""Construir o contexto partilhado para fatura e email."""
	_garantir_numero_fatura(encomenda)
	itens = list(encomenda.itens.select_related('produto').all())
	return {
		'encomenda': encomenda,
		'cliente': encomenda.cliente,
		'itens': itens,
		'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		'data_fatura': timezone.localtime(encomenda.data_pagamento or encomenda.data_criacao),
	}


def _formatar_moeda_pdf(valor):
	"""Formatar valor monetário para PDF."""
	if valor is None:
		valor = Decimal('0.00')
	return f'{Decimal(valor):.2f} €'


def _gerar_pdf_fatura_bytes(encomenda):
	"""Gerar o conteúdo PDF da fatura."""
	contexto = _contexto_fatura_encomenda(encomenda)
	rp = _import_reportlab()
	colors = rp['colors']
	TA_LEFT = rp['TA_LEFT']
	TA_CENTER = rp['TA_CENTER']
	TA_RIGHT = rp['TA_RIGHT']
	A4 = rp['A4']
	ParagraphStyle = rp['ParagraphStyle']
	getSampleStyleSheet = rp['getSampleStyleSheet']
	mm = rp['mm']
	Paragraph = rp['Paragraph']
	SimpleDocTemplate = rp['SimpleDocTemplate']
	Spacer = rp['Spacer']
	Table = rp['Table']
	TableStyle = rp['TableStyle']

	buffer = BytesIO()
	doc = SimpleDocTemplate(
		buffer,
		pagesize=A4,
		leftMargin=18 * mm,
		rightMargin=18 * mm,
		topMargin=18 * mm,
		bottomMargin=18 * mm,
		title=f'Fatura {encomenda.numero_fatura}',
		author='WellReserve',
		subject=f'Fatura da encomenda #{encomenda.pk}',
	)

	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(name='InvoiceTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=colors.HexColor('#1a5f7a'), alignment=TA_LEFT, spaceAfter=6))
	styles.add(ParagraphStyle(name='InvoiceSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#6b7280')))
	styles.add(ParagraphStyle(name='SectionLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#374151'), leading=11, spaceAfter=4))
	styles.add(ParagraphStyle(name='SmallText', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#111827')))
	styles.add(ParagraphStyle(name='RightSmallText', parent=styles['SmallText'], alignment=TA_RIGHT))
	styles.add(ParagraphStyle(name='CenterSmallText', parent=styles['SmallText'], alignment=TA_CENTER))

	elements = []

	header_table = Table([
		[
			[
				Paragraph('WellReserve', styles['InvoiceTitle']),
				Paragraph('Fatura da encomenda', styles['InvoiceSubtitle']),
				Spacer(1, 2),
				Paragraph(f'Encomenda #{encomenda.pk}', styles['SmallText']),
			],
			[
				Paragraph(f'<b>Fatura:</b> {escape(encomenda.numero_fatura)}', styles['SmallText']),
				Paragraph(f'<b>Data:</b> {contexto["data_fatura"].strftime("%d/%m/%Y %H:%M")}', styles['SmallText']),
				Paragraph(f'<b>Pagamento:</b> {encomenda.get_estado_pagamento_display()}', styles['SmallText']),
				Paragraph(f'<b>Método:</b> {encomenda.get_metodo_pagamento_display()}', styles['SmallText']),
			],
		]
	], colWidths=[100 * mm, 60 * mm])
	header_table.setStyle(TableStyle([
		('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
		('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
		('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
		('VALIGN', (0, 0), (-1, -1), 'TOP'),
		('LEFTPADDING', (0, 0), (-1, -1), 10),
		('RIGHTPADDING', (0, 0), (-1, -1), 10),
		('TOPPADDING', (0, 0), (-1, -1), 10),
		('BOTTOMPADDING', (0, 0), (-1, -1), 10),
	]))
	elements.append(header_table)
	elements.append(Spacer(1, 10))

	info_table = Table([
		[Paragraph('Dados de faturação', styles['SectionLabel']), Paragraph('Resumo de pagamento', styles['SectionLabel'])],
		[
			Paragraph(
				f"<b>{escape(encomenda.faturacao_nome or contexto['cliente'].get_full_name() or contexto['cliente'].username)}</b><br/>"
				f"{escape(encomenda.faturacao_email)}<br/>"
				f"NIF: {escape(encomenda.faturacao_nif or '-')}<br/>"
				f"Morada: {escape(encomenda.faturacao_morada).replace(chr(10), '<br/>') if encomenda.faturacao_morada else '-'}",
				styles['SmallText']
			),
			Paragraph(
				f"<b>Estado:</b> {encomenda.get_estado_pagamento_display()}<br/>"
				f"<b>Referência:</b> {escape(encomenda.referencia_pagamento or '-')}<br/>"
				f"<b>Data de pagamento:</b> {(encomenda.data_pagamento and timezone.localtime(encomenda.data_pagamento).strftime('%d/%m/%Y %H:%M')) or '-'}",
				styles['SmallText']
			),
		],
	], colWidths=[88 * mm, 88 * mm])
	info_table.setStyle(TableStyle([
		('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eff6ff')),
		('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
		('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
		('VALIGN', (0, 0), (-1, -1), 'TOP'),
		('LEFTPADDING', (0, 0), (-1, -1), 10),
		('RIGHTPADDING', (0, 0), (-1, -1), 10),
		('TOPPADDING', (0, 0), (-1, -1), 8),
		('BOTTOMPADDING', (0, 0), (-1, -1), 8),
	]))
	elements.append(info_table)
	elements.append(Spacer(1, 12))

	item_rows = [[
		Paragraph('<b>Produto</b>', styles['SmallText']),
		Paragraph('<b>Qtd</b>', styles['CenterSmallText']),
		Paragraph('<b>Preço Unitário</b>', styles['RightSmallText']),
		Paragraph('<b>Subtotal</b>', styles['RightSmallText']),
	]]

	for item in contexto['itens']:
		item_rows.append([
			Paragraph(f"<b>{escape(item.produto.nome)}</b><br/><font color='#6b7280'>{escape((item.produto.descricao or '')[:120])}</font>", styles['SmallText']),
			Paragraph(str(item.quantidade), styles['CenterSmallText']),
			Paragraph(_formatar_moeda_pdf(item.preco_unitario), styles['RightSmallText']),
			Paragraph(_formatar_moeda_pdf(item.subtotal), styles['RightSmallText']),
		])

	items_table = Table(item_rows, colWidths=[92 * mm, 16 * mm, 32 * mm, 34 * mm], repeatRows=1)
	items_table.setStyle(TableStyle([
		('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5f7a')),
		('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
		('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
		('FONTSIZE', (0, 0), (-1, 0), 9),
		('LEADING', (0, 0), (-1, 0), 11),
		('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
		('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
		('VALIGN', (0, 0), (-1, -1), 'TOP'),
		('ALIGN', (1, 1), (1, -1), 'CENTER'),
		('ALIGN', (2, 1), (3, -1), 'RIGHT'),
		('BACKGROUND', (0, 1), (-1, -1), colors.white),
		('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
		('LEFTPADDING', (0, 0), (-1, -1), 8),
		('RIGHTPADDING', (0, 0), (-1, -1), 8),
		('TOPPADDING', (0, 0), (-1, -1), 7),
		('BOTTOMPADDING', (0, 0), (-1, -1), 7),
	]))
	elements.append(items_table)
	elements.append(Spacer(1, 12))

	totals_table = Table([
		[Paragraph('<b>Subtotal</b>', styles['SmallText']), Paragraph(_formatar_moeda_pdf(encomenda.total), styles['RightSmallText'])],
		[Paragraph('<b>Total</b>', styles['SmallText']), Paragraph(_formatar_moeda_pdf(encomenda.total), styles['RightSmallText'])],
	], colWidths=[30 * mm, 36 * mm])
	totals_table.setStyle(TableStyle([
		('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
		('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ecfeff')),
		('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f9fafb')),
		('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
		('ALIGN', (1, 0), (1, -1), 'RIGHT'),
		('LEFTPADDING', (0, 0), (-1, -1), 8),
		('RIGHTPADDING', (0, 0), (-1, -1), 8),
		('TOPPADDING', (0, 0), (-1, -1), 7),
		('BOTTOMPADDING', (0, 0), (-1, -1), 7),
	]))
	elements.append(totals_table)

	footer = Paragraph('Documento gerado automaticamente pela plataforma WellReserve.', styles['InvoiceSubtitle'])
	elements.append(Spacer(1, 14))
	elements.append(footer)

	doc.build(elements)
	pdf = buffer.getvalue()
	buffer.close()
	return pdf


def enviar_email_fatura_encomenda(encomenda):
	"""Enviar email com a fatura da encomenda."""
	try:
		destinatario = (encomenda.cliente.email or encomenda.faturacao_email or '').strip()
		if not destinatario:
			logger.warning('Encomenda #%s sem email de destinatário para envio de fatura.', encomenda.pk)
			return False

		contexto = _contexto_fatura_encomenda(encomenda)

		html_message = render_to_string('emails/encomenda_fatura.html', contexto)
		text_message = render_to_string('emails/encomenda_fatura.txt', contexto)
		pdf_bytes = _gerar_pdf_fatura_bytes(encomenda)

		message = EmailMultiAlternatives(
			subject=f'Fatura da Encomenda - #{encomenda.pk}',
			body=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			to=[destinatario],
		)
		message.attach_alternative(html_message, 'text/html')
		message.attach(f'{encomenda.numero_fatura}.pdf', pdf_bytes, 'application/pdf')
		message.send(fail_silently=False)
		logger.info(f'Email de fatura enviado para {destinatario} (Encomenda #{encomenda.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de fatura da encomenda: {e}')
		return False


def enviar_email_confirmacao_encomenda(encomenda):
	"""Enviar email ao utilizador quando a encomenda é confirmada"""
	try:
		destinatario = (encomenda.cliente.email or encomenda.faturacao_email or '').strip()
		if not destinatario:
			logger.warning('Encomenda #%s sem email de destinatário para envio de confirmação.', encomenda.pk)
			return False

		contexto = {
			'encomenda': encomenda,
			'cliente': encomenda.cliente,
			'itens': encomenda.itens.select_related('produto').all(),
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/encomenda_confirmada.html', contexto)
		text_message = render_to_string('emails/encomenda_confirmada.txt', contexto)

		send_mail(
			subject=f'Encomenda Confirmada - #{encomenda.pk}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[destinatario],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de confirmação de encomenda enviado para {destinatario} (Encomenda #{encomenda.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de confirmação de encomenda: {e}')
		return False


def enviar_email_alteracao_estado_encomenda(encomenda, estado_antigo, estado_novo):
	"""Enviar email ao utilizador quando o estado da encomenda muda"""
	try:
		destinatario = (encomenda.cliente.email or encomenda.faturacao_email or '').strip()
		if not destinatario:
			logger.warning('Encomenda #%s sem email de destinatário para alteração de estado.', encomenda.pk)
			return False

		contexto = {
			'encomenda': encomenda,
			'cliente': encomenda.cliente,
			'estado_antigo': estado_antigo,
			'estado_novo': estado_novo,
			'estado_antigo_label': dict(Encomenda.ESTADO_CHOICES).get(estado_antigo, estado_antigo),
			'estado_novo_label': dict(Encomenda.ESTADO_CHOICES).get(estado_novo, estado_novo),
			'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
		}

		html_message = render_to_string('emails/encomenda_estado_alterado.html', contexto)
		text_message = render_to_string('emails/encomenda_estado_alterado.txt', contexto)

		send_mail(
			subject=f'Estado da Encomenda Atualizado - #{encomenda.pk}',
			message=text_message,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[destinatario],
			html_message=html_message,
			fail_silently=False,
		)
		logger.info(f'Email de alteração de estado enviado para {destinatario} (Encomenda #{encomenda.pk})')
		return True
	except Exception as e:
		logger.error(f'Erro ao enviar email de alteração de estado da encomenda: {e}')
		return False


@login_required
def finalizar_encomenda(request):
	"""Finalizar encomenda"""
	carrinho_session = request.session.get('carrinho', {})

	if not carrinho_session:
		messages.error(request, 'O seu carrinho está vazio.')
		return redirect('produtos_lista')

	if request.method == 'POST':
		form = CheckoutEncomendaForm(request.POST)
		if form.is_valid():
			dados = form.cleaned_data
			metodo_pagamento = dados['metodo_pagamento']
			pagamento_simulado = metodo_pagamento == 'simulado'

			encomenda = Encomenda.objects.create(
				cliente=request.user,
				notas=dados.get('notas', ''),
				faturacao_nome=dados['faturacao_nome'],
				faturacao_email=dados['faturacao_email'],
				faturacao_nif=dados['faturacao_nif'],
				faturacao_morada=dados['faturacao_morada'],
				entrega_morada=dados['entrega_morada'],
				metodo_pagamento=metodo_pagamento,
				estado_pagamento='pago' if pagamento_simulado else 'pendente',
				data_pagamento=timezone.now() if pagamento_simulado else None,
				referencia_pagamento=(
					f'FP-{timezone.localtime().strftime("%Y%m%d")}-{request.user.pk:04d}-{timezone.localtime().strftime("%H%M%S")}'
					if pagamento_simulado else ''
				),
			)

			for produto_id, quantidade in carrinho_session.items():
				try:
					produto = Produto.objects.get(pk=produto_id, ativo=True)
					ItemEncomenda.objects.create(
						encomenda=encomenda,
						produto=produto,
						quantidade=quantidade,
						preco_unitario=produto.preco
					)
					produto.stock -= quantidade
					produto.save()
				except Produto.DoesNotExist:
					pass

			encomenda.calcular_total()
			_garantir_numero_fatura(encomenda)
			request.session['carrinho'] = {}

			email_confirmacao_enviado = False
			email_fatura_enviado = False

			try:
				email_confirmacao_enviado = enviar_email_confirmacao_encomenda(encomenda)
			except Exception:
				logger.exception('Falha inesperada ao enviar email de confirmação da encomenda #%s', encomenda.pk)
				email_confirmacao_enviado = False

			if pagamento_simulado:
				try:
					email_fatura_enviado = enviar_email_fatura_encomenda(encomenda)
				except Exception:
					logger.exception('Falha inesperada ao enviar fatura por email da encomenda #%s', encomenda.pk)
					email_fatura_enviado = False

			if pagamento_simulado:
				if email_confirmacao_enviado and email_fatura_enviado:
					messages.success(request, f'Pagamento fictício aprovado e encomenda #{encomenda.pk} criada com sucesso. O email de confirmação e a fatura foram enviados.')
				elif email_confirmacao_enviado:
					messages.success(request, f'Pagamento fictício aprovado e encomenda #{encomenda.pk} criada com sucesso. O email de confirmação foi enviado. (Erro ao enviar a fatura por email)')
				elif email_fatura_enviado:
					messages.success(request, f'Pagamento fictício aprovado e encomenda #{encomenda.pk} criada com sucesso. A fatura foi enviada. (Erro ao enviar email de confirmação)')
				else:
					messages.success(request, f'Pagamento fictício aprovado e encomenda #{encomenda.pk} criada com sucesso. (Erro ao enviar email de confirmação e fatura)')
			else:
				if email_confirmacao_enviado:
					messages.success(request, f'Encomenda #{encomenda.pk} criada com sucesso! O email de confirmação foi enviado. O pagamento será efetuado na receção.')
				else:
					messages.success(request, f'Encomenda #{encomenda.pk} criada com sucesso! O pagamento será efetuado na receção. (Erro ao enviar email de confirmação)')
			return redirect('encomenda_detalhe', pk=encomenda.pk)
	else:
		form = CheckoutEncomendaForm(initial={
			'faturacao_nome': request.user.get_full_name() or request.user.username,
			'faturacao_email': request.user.email,
			'faturacao_nif': getattr(request.user, 'nif', '') or '',
			'faturacao_morada': getattr(request.user, 'morada', '') or '',
			'entrega_morada': getattr(request.user, 'morada', '') or '',
			'metodo_pagamento': 'simulado',
		})

	itens = []
	total = 0

	for produto_id, quantidade in carrinho_session.items():
		try:
			produto = Produto.objects.get(pk=produto_id, ativo=True)
			subtotal = produto.preco * quantidade
			itens.append({'produto': produto, 'quantidade': quantidade, 'subtotal': subtotal})
			total += subtotal
		except Produto.DoesNotExist:
			pass

	context = {
		'itens': itens,
		'total': total,
		'form': form,
	}
	return render(request, 'produtos/finalizar.html', context)


@login_required
def encomendas_lista(request):
	"""Lista de encomendas do utilizador"""
	if request.user.is_admin or request.user.is_funcionario or request.user.is_recepcao:
		encomendas = Encomenda.objects.select_related('cliente').all()
	else:
		encomendas = Encomenda.objects.filter(cliente=request.user)

	encomendas = encomendas.order_by('-data_criacao')

	paginator = Paginator(encomendas, 20)
	page = request.GET.get('page')
	encomendas = paginator.get_page(page)

	return render(request, 'produtos/encomendas_lista.html', {'encomendas': encomendas})


@login_required
def encomenda_detalhe(request, pk):
	"""Detalhe de uma encomenda"""
	if request.user.is_admin or request.user.is_funcionario or request.user.is_recepcao:
		encomenda = get_object_or_404(Encomenda, pk=pk)
	else:
		encomenda = get_object_or_404(Encomenda, pk=pk, cliente=request.user)

	_garantir_numero_fatura(encomenda)

	return render(request, 'produtos/encomenda_detalhe.html', {
		'encomenda': encomenda,
		'estado_choices': Encomenda.ESTADO_CHOICES,
	})


@login_required
def encomenda_fatura(request, pk):
	"""Ver fatura da encomenda na app."""
	if request.user.is_admin or request.user.is_funcionario or request.user.is_recepcao:
		encomenda = get_object_or_404(Encomenda, pk=pk)
	else:
		encomenda = get_object_or_404(Encomenda, pk=pk, cliente=request.user)

	contexto = _contexto_fatura_encomenda(encomenda)
	return render(request, 'produtos/fatura.html', contexto)


@login_required
def encomenda_fatura_pdf(request, pk):
	"""Exportar fatura em PDF."""
	if request.user.is_admin or request.user.is_funcionario or request.user.is_recepcao:
		encomenda = get_object_or_404(Encomenda, pk=pk)
	else:
		encomenda = get_object_or_404(Encomenda, pk=pk, cliente=request.user)

	pdf_bytes = _gerar_pdf_fatura_bytes(encomenda)
	response = HttpResponse(content_type='application/pdf')
	download = request.GET.get('download') == '1'
	disposition = 'attachment' if download else 'inline'
	response['Content-Disposition'] = f'{disposition}; filename="{encomenda.numero_fatura}.pdf"'
	response.write(pdf_bytes)
	return response


@recepcao_funcionario_required
def encomenda_atualizar_estado(request, pk):
	"""Atualizar estado da encomenda"""
	encomenda = get_object_or_404(Encomenda, pk=pk)

	if request.method == 'POST':
		novo_estado = request.POST.get('estado')
		if novo_estado in dict(Encomenda.ESTADO_CHOICES):
			estado_antigo = encomenda.estado
			encomenda.estado = novo_estado
			encomenda.save()
			email_enviado = False
			if estado_antigo != novo_estado:
				email_enviado = enviar_email_alteracao_estado_encomenda(encomenda, estado_antigo, novo_estado)

			if email_enviado:
				messages.success(request, 'Estado da encomenda atualizado e cliente notificado por email!')
			elif estado_antigo != novo_estado:
				messages.success(request, 'Estado da encomenda atualizado. (Erro ao enviar email ao cliente)')
			else:
				messages.success(request, 'Estado da encomenda atualizado!')

	return redirect('encomenda_detalhe', pk=pk)
