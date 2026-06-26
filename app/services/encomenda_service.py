"""Services de encomendas da WellReserve."""
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.utils import timezone

from ..models import Encomenda, ItemEncomenda, Produto


def _import_reportlab():
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
    except ImportError as exc:
        raise ImportError('reportlab is required to generate PDFs. Install it with `pip install reportlab`.') from exc


class EncomendaService:
    """Operações de negócio relacionadas com encomendas."""

    @staticmethod
    def garantir_numero_fatura(encomenda):
        if not encomenda.numero_fatura:
            data_base = timezone.localtime(encomenda.data_criacao) if encomenda.data_criacao else timezone.localtime()
            encomenda.numero_fatura = f'FAT-{data_base.strftime("%Y%m%d")}-{encomenda.pk:05d}'
            encomenda.save(update_fields=['numero_fatura'])
        return encomenda.numero_fatura

    @staticmethod
    def contexto_fatura(encomenda):
        EncomendaService.garantir_numero_fatura(encomenda)
        itens = list(encomenda.itens.select_related('produto').all())
        return {
            'encomenda': encomenda,
            'cliente': encomenda.cliente,
            'itens': itens,
            'contacto_email': settings.CONTACTO_EMAIL_DESTINO,
            'data_fatura': timezone.localtime(encomenda.data_pagamento or encomenda.data_criacao),
        }

    @staticmethod
    def formatar_moeda_pdf(valor):
        if valor is None:
            valor = Decimal('0.00')
        return f'{Decimal(valor):.2f} €'

    @staticmethod
    def gerar_pdf_fatura_bytes(encomenda):
        contexto = EncomendaService.contexto_fatura(encomenda)
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
                    f"NIF: {escape(encomenda.faturacao_nif or '-') }<br/>"
                    f"Morada: {escape(encomenda.faturacao_morada).replace(chr(10), '<br/>') if encomenda.faturacao_morada else '-'}",
                    styles['SmallText'],
                ),
                Paragraph(
                    f"<b>Estado:</b> {encomenda.get_estado_pagamento_display()}<br/>"
                    f"<b>Referência:</b> {escape(encomenda.referencia_pagamento or '-')}<br/>"
                    f"<b>Data de pagamento:</b> {(encomenda.data_pagamento and timezone.localtime(encomenda.data_pagamento).strftime('%d/%m/%Y %H:%M')) or '-'}",
                    styles['SmallText'],
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
                Paragraph(EncomendaService.formatar_moeda_pdf(item.preco_unitario), styles['RightSmallText']),
                Paragraph(EncomendaService.formatar_moeda_pdf(item.subtotal), styles['RightSmallText']),
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
            [Paragraph('<b>Subtotal</b>', styles['SmallText']), Paragraph(EncomendaService.formatar_moeda_pdf(encomenda.total), styles['RightSmallText'])],
            [Paragraph('<b>Total</b>', styles['SmallText']), Paragraph(EncomendaService.formatar_moeda_pdf(encomenda.total), styles['RightSmallText'])],
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

    @staticmethod
    def criar_encomenda(cliente, carrinho_session, dados, referencia_pagamento='', pagamento_simulado=False):
        encomenda = Encomenda.objects.create(
            cliente=cliente,
            notas=dados.get('notas', ''),
            faturacao_nome=dados['faturacao_nome'],
            faturacao_email=dados['faturacao_email'],
            faturacao_nif=dados['faturacao_nif'],
            faturacao_morada=dados['faturacao_morada'],
            entrega_morada=dados['entrega_morada'],
            metodo_pagamento=dados['metodo_pagamento'],
            estado_pagamento='pago' if pagamento_simulado else 'pendente',
            data_pagamento=timezone.now() if pagamento_simulado else None,
            referencia_pagamento=referencia_pagamento,
        )

        for produto_id, quantidade in carrinho_session.items():
            try:
                produto = Produto.objects.get(pk=produto_id, ativo=True)
            except Produto.DoesNotExist:
                continue

            ItemEncomenda.objects.create(
                encomenda=encomenda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=produto.preco,
            )
            produto.stock -= quantidade
            produto.save()

        encomenda.calcular_total()
        EncomendaService.garantir_numero_fatura(encomenda)
        return encomenda
