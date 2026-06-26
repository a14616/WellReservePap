"""Services de utilizadores da WellReserve."""
from .email_service import EmailService


class UtilizadorService:
    """Operações associadas a utilizadores."""

    @staticmethod
    def enviar_boas_vindas(utilizador):
        return EmailService.enviar_boas_vindas(utilizador)
