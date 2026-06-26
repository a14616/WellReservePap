"""
Admin - WellReserve
Configuração do painel de administração Django
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilizador, CategoriaServico, Servico, HorarioFuncionario,
    FeriasFuncionario, Reserva, CategoriaProduto, Produto,
    Encomenda, ItemEncomenda, Configuracao, Contacto
)
from .services import EmailService


# Configuração do site admin
admin.site.site_header = 'WellReserve - Administração'
admin.site.site_title = 'WellReserve Admin'
admin.site.index_title = 'Painel de Administração'


@admin.register(Utilizador)
class UtilizadorAdmin(UserAdmin):
    """Admin para Utilizadores"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo', 'is_active', 'date_joined']
    list_filter = ['tipo', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telefone']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('tipo', 'telefone', 'morada', 'data_nascimento', 'nif', 'foto')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Adicionais', {
            'fields': ('tipo', 'email', 'first_name', 'last_name', 'telefone')
        }),
    )


@admin.register(CategoriaServico)
class CategoriaServicoAdmin(admin.ModelAdmin):
    """Admin para Categorias de Serviço"""
    list_display = ['nome', 'icone', 'ordem', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    ordering = ['ordem', 'nome']
    list_editable = ['ordem', 'ativo']


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    """Admin para Serviços"""
    list_display = ['nome', 'categoria', 'duracao', 'preco', 'capacidade_maxima', 'ativo', 'destaque']
    list_filter = ['categoria', 'ativo', 'destaque', 'requer_prescricao']
    search_fields = ['nome', 'descricao']
    ordering = ['categoria', 'nome']
    list_editable = ['ativo', 'destaque']
    filter_horizontal = ['funcionarios']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'categoria', 'imagem')
        }),
        ('Detalhes', {
            'fields': ('duracao', 'preco', 'capacidade_maxima', 'requer_prescricao')
        }),
        ('Funcionários', {
            'fields': ('funcionarios',)
        }),
        ('Estado', {
            'fields': ('ativo', 'destaque')
        }),
    )


@admin.register(HorarioFuncionario)
class HorarioFuncionarioAdmin(admin.ModelAdmin):
    """Admin para Horários de Funcionários"""
    list_display = ['funcionario', 'dia_semana', 'hora_inicio', 'hora_fim', 'estado', 'ativo']
    list_filter = ['funcionario', 'dia_semana', 'estado', 'ativo']
    ordering = ['funcionario', 'dia_semana', 'hora_inicio']
    list_editable = ['estado', 'ativo']


@admin.register(FeriasFuncionario)
class FeriasFuncionarioAdmin(admin.ModelAdmin):
    """Admin para Férias de Funcionários"""
    list_display = ['funcionario', 'data_inicio', 'data_fim', 'motivo', 'estado']
    list_filter = ['funcionario', 'data_inicio', 'estado']
    search_fields = ['funcionario__username', 'funcionario__first_name', 'motivo']
    ordering = ['-data_inicio']
    date_hierarchy = 'data_inicio'


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """Admin para Reservas"""
    list_display = ['id', 'cliente', 'servico', 'funcionario', 'data', 'hora', 'estado', 'preco_final']
    list_filter = ['estado', 'servico', 'funcionario', 'data']
    search_fields = ['cliente__username', 'cliente__first_name', 'cliente__last_name', 'servico__nome']
    ordering = ['-data', '-hora']
    date_hierarchy = 'data'
    list_editable = ['estado']
    raw_id_fields = ['cliente', 'funcionario']
    
    fieldsets = (
        ('Cliente e Serviço', {
            'fields': ('cliente', 'servico', 'funcionario')
        }),
        ('Data e Hora', {
            'fields': ('data', 'hora')
        }),
        ('Estado e Preço', {
            'fields': ('estado', 'preco_final')
        }),
        ('Notas', {
            'fields': ('notas', 'notas_internas'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    """Admin para Categorias de Produto"""
    list_display = ['nome', 'ordem', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    ordering = ['ordem', 'nome']
    list_editable = ['ordem', 'ativo']


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    """Admin para Produtos"""
    list_display = ['nome', 'categoria', 'preco', 'stock', 'ativo', 'destaque']
    list_filter = ['categoria', 'ativo', 'destaque']
    search_fields = ['nome', 'descricao']
    ordering = ['categoria', 'nome']
    list_editable = ['preco', 'stock', 'ativo', 'destaque']


class ItemEncomendaInline(admin.TabularInline):
    """Inline para Itens de Encomenda"""
    model = ItemEncomenda
    extra = 0
    readonly_fields = ['subtotal']
    
    def subtotal(self, obj):
        return f'{obj.subtotal}€'
    subtotal.short_description = 'Subtotal'


@admin.register(Encomenda)
class EncomendaAdmin(admin.ModelAdmin):
    """Admin para Encomendas"""
    list_display = ['id', 'cliente', 'estado', 'estado_pagamento', 'total', 'data_criacao']
    list_filter = ['estado', 'estado_pagamento', 'data_criacao']
    search_fields = ['cliente__username', 'cliente__first_name', 'cliente__last_name']
    ordering = ['-data_criacao']
    date_hierarchy = 'data_criacao'
    list_editable = ['estado', 'estado_pagamento']
    raw_id_fields = ['cliente']
    inlines = [ItemEncomendaInline]
    readonly_fields = ['total', 'data_criacao', 'data_atualizacao', 'numero_fatura', 'referencia_pagamento', 'data_pagamento']
    fieldsets = (
        ('Cliente', {
            'fields': ('cliente',)
        }),
        ('Estado', {
            'fields': ('estado', 'estado_pagamento')
        }),
        ('Pagamentos e Fatura', {
            'fields': ('total', 'numero_fatura', 'referencia_pagamento', 'data_pagamento')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )

    def save_model(self, request, obj, form, change):
        estado_antigo = None
        estado_pagamento_antigo = None
        if change and obj.pk:
            estado_antigo = Encomenda.objects.filter(pk=obj.pk).values_list('estado', flat=True).first()
            estado_pagamento_antigo = Encomenda.objects.filter(pk=obj.pk).values_list('estado_pagamento', flat=True).first()

        super().save_model(request, obj, form, change)

        if estado_antigo and estado_antigo != obj.estado:
            EmailService.enviar_alteracao_estado_encomenda(obj, estado_antigo, obj.estado)

        if estado_pagamento_antigo and estado_pagamento_antigo != obj.estado_pagamento and obj.estado_pagamento == 'pago':
            if not obj.data_pagamento:
                from django.utils import timezone
                obj.data_pagamento = timezone.now()
                obj.save(update_fields=['data_pagamento'])
            EmailService.enviar_fatura_encomenda(obj)


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    """Admin para Configurações"""
    list_display = ['chave', 'valor', 'descricao']
    search_fields = ['chave', 'valor', 'descricao']
    ordering = ['chave']


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    """Admin para Contactos"""
    list_display = ['nome', 'email', 'assunto', 'lida', 'respondida', 'data_criacao']
    list_filter = ['lida', 'respondida', 'data_criacao']
    search_fields = ['nome', 'email', 'assunto', 'mensagem']
    ordering = ['-data_criacao']
    date_hierarchy = 'data_criacao'
    list_editable = ['lida', 'respondida']
    readonly_fields = ['data_criacao']
    
    fieldsets = (
        ('Remetente', {
            'fields': ('nome', 'email', 'telefone')
        }),
        ('Mensagem', {
            'fields': ('assunto', 'mensagem')
        }),
        ('Estado', {
            'fields': ('lida', 'respondida', 'data_criacao')
        }),
    )
