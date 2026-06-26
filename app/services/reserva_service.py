"""Services de reservas da WellReserve."""
from django.db.models import Q

from ..models import Reserva
from .email_service import EmailService


class ReservaService:
    """Operações de negócio relacionadas com reservas."""

    @staticmethod
    def criar_reserva(form, user):
        reserva = form.save(commit=False)
        if not (user.is_recepcao or user.is_admin):
            reserva.cliente = user
        reserva.save()
        return reserva

    @staticmethod
    def cancelar_reserva(reserva, cancelado_pelo_cliente=False):
        reserva.estado = 'cancelada'
        reserva.save(update_fields=['estado'])
        return EmailService.enviar_cancelamento_reserva(reserva, cancelado_pelo_cliente=cancelado_pelo_cliente)

    @staticmethod
    def confirmar_reserva(reserva):
        reserva.estado = 'confirmada'
        reserva.save(update_fields=['estado'])
        return EmailService.enviar_confirmacao_reserva(reserva)

    @staticmethod
    def concluir_reserva(reserva):
        reserva.estado = 'concluida'
        reserva.save(update_fields=['estado'])
        return EmailService.enviar_conclusao_reserva(reserva)

    @staticmethod
    def marcar_nao_compareceu(reserva):
        reserva.estado = 'nao_compareceu'
        reserva.save(update_fields=['estado'])
        return EmailService.enviar_nao_compareceu_reserva(reserva)

    @staticmethod
    def reservas_em_conflito_horario(funcionario, dia_semana, hora_inicio, hora_fim):
        return Reserva.objects.filter(
            funcionario=funcionario,
            data__week_day=dia_semana,
        ).filter(
            Q(hora__lt=hora_fim) & Q(hora__gte=hora_inicio)
        ).first()
