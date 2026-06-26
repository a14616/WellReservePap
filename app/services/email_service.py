"""Services de email da WellReserve."""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

from ..models import Encomenda, Utilizador


class EmailService:
    """Envio de emails transacionais."""

    @staticmethod
    def _formatar_valor_alteracao(valor):
        if valor is None:
            return 'vazio'
        if hasattr(valor, 'strftime'):
            if hasattr(valor, 'hour') and hasattr(valor, 'minute'):
                return valor.strftime('%H:%M')
            return valor.strftime('%d/%m/%Y')
        if hasattr(valor, 'get_full_name'):
            return valor.get_full_name() or valor.username
        return str(valor)

    @staticmethod
    def enviar_confirmacao_reserva(reserva):
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_cancelamento_reserva(reserva, cancelado_pelo_cliente=False):
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_alteracao_reserva(reserva, alteracoes):
        try:
            alteracoes_formatadas = [
                {
                    'rotulo': alteracao['rotulo'],
                    'antigo': EmailService._formatar_valor_alteracao(alteracao['antigo']),
                    'novo': EmailService._formatar_valor_alteracao(alteracao['novo']),
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_boas_vindas(utilizador: Utilizador):
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

    @staticmethod
    def enviar_conclusao_reserva(reserva):
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_nao_compareceu_reserva(reserva):
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_confirmacao_encomenda(encomenda: Encomenda):
        try:
            destinatario = encomenda.cliente.email or encomenda.faturacao_email
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_alteracao_estado_encomenda(encomenda: Encomenda, estado_antigo, estado_novo):
        try:
            destinatario = encomenda.cliente.email or encomenda.faturacao_email
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
            return True
        except Exception:
            return False

    @staticmethod
    def enviar_fatura_encomenda(encomenda: Encomenda):
        try:
            from .encomenda_service import EncomendaService

            destinatario = encomenda.cliente.email or encomenda.faturacao_email
            contexto = EncomendaService.contexto_fatura(encomenda)
            html_message = render_to_string('emails/encomenda_fatura.html', contexto)
            text_message = render_to_string('emails/encomenda_fatura.txt', contexto)
            pdf_bytes = EncomendaService.gerar_pdf_fatura_bytes(encomenda)

            message = EmailMultiAlternatives(
                subject=f'Fatura da Encomenda - #{encomenda.pk}',
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinatario],
            )
            message.attach_alternative(html_message, 'text/html')
            message.attach(f'{encomenda.numero_fatura}.pdf', pdf_bytes, 'application/pdf')
            message.send(fail_silently=False)
            return True
        except Exception:
            return False
