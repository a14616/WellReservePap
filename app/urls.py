"""
URLs - WellReserve
"""
from django.urls import path
from . import views

urlpatterns = [
    # Páginas públicas
    path('', views.home, name='home'),
    path('sobre/', views.sobre, name='sobre'),
    path('contacto/', views.contacto, name='contacto'),
    
    # Autenticação
    path('registo/', views.registo, name='registo'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Saúde da aplicação
    path('healthz/', views.health_check, name='health_check'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/alterar-password/', views.alterar_password, name='alterar_password'),
    
    # Serviços (público)
    path('servicos/', views.servicos_lista, name='servicos_lista'),
    path('servicos/<int:pk>/', views.servico_detalhe, name='servico_detalhe'),
    
    # Reservas
    path('reservas/', views.reservas_lista, name='reservas_lista'),
    path('reservas/minhas/', views.minhas_reservas, name='minhas_reservas'),
    path('reservas/criar/', views.reserva_criar, name='reserva_criar'),
        path('reservas/funcionario/<int:pk>/', views.reservas_funcionario, name='reservas_funcionario'),
    path('reservas/<int:pk>/', views.reserva_detalhe, name='reserva_detalhe'),
    path('reservas/<int:pk>/cancelar/', views.reserva_cancelar, name='reserva_cancelar'),
    path('reservas/<int:pk>/editar/', views.reserva_editar, name='reserva_editar'),
    path('reservas/<int:pk>/confirmar/', views.reserva_confirmar, name='reserva_confirmar'),
    path('reservas/<int:pk>/concluir/', views.reserva_concluir, name='reserva_concluir'),
    path('reservas/<int:pk>/nao-compareceu/', views.reserva_nao_compareceu, name='reserva_nao_compareceu'),
    
    # Produtos (público)
    path('produtos/', views.produtos_lista, name='produtos_lista'),
    path('produtos/<int:pk>/', views.produto_detalhe, name='produto_detalhe'),
    
    # Carrinho e Encomendas
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/adicionar/<int:pk>/', views.carrinho_adicionar, name='carrinho_adicionar'),
    path('carrinho/remover/<int:pk>/', views.carrinho_remover, name='carrinho_remover'),
    path('carrinho/atualizar/', views.carrinho_atualizar, name='carrinho_atualizar'),
    path('carrinho/limpar/', views.carrinho_limpar, name='carrinho_limpar'),
    path('carrinho/finalizar/', views.finalizar_encomenda, name='finalizar_encomenda'),
    path('encomenda/criar/', views.finalizar_encomenda, name='encomenda_criar'),
    path('encomendas/', views.encomendas_lista, name='encomendas_lista'),
    path('encomendas/<int:pk>/', views.encomenda_detalhe, name='encomenda_detalhe'),
    path('encomendas/<int:pk>/fatura/', views.encomenda_fatura, name='encomenda_fatura'),
    path('encomendas/<int:pk>/fatura/pdf/', views.encomenda_fatura_pdf, name='encomenda_fatura_pdf'),
    path('encomendas/<int:pk>/estado/', views.encomenda_atualizar_estado, name='encomenda_atualizar_estado'),
    
    # API
    path('api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('api/procurar-clientes/', views.api_procurar_clientes, name='api_procurar_clientes'),
    
    # ============================================
    # ADMINISTRAÇÃO
    # ============================================
    
    # Gestão de Serviços
    path('gestao/servicos/', views.servicos_gestao, name='servicos_gestao'),
    path('gestao/servicos/criar/', views.servico_criar, name='servico_criar'),
    path('gestao/servicos/<int:pk>/editar/', views.servico_editar, name='servico_editar'),
    path('gestao/servicos/<int:pk>/eliminar/', views.servico_eliminar, name='servico_eliminar'),
    
    # Gestão de Produtos
    path('gestao/produtos/', views.produtos_gestao, name='produtos_gestao'),
    path('gestao/produtos/criar/', views.produto_criar, name='produto_criar'),
    path('gestao/produtos/<int:pk>/editar/', views.produto_editar, name='produto_editar'),
    path('gestao/produtos/<int:pk>/eliminar/', views.produto_eliminar, name='produto_eliminar'),
    
    # Gestão de Utilizadores
    path('gestao/utilizadores/', views.utilizadores_lista, name='utilizadores_lista'),
    path('gestao/utilizadores/criar/', views.utilizador_criar, name='utilizador_criar'),
    path('gestao/utilizadores/<int:pk>/', views.utilizador_detalhe, name='utilizador_detalhe'),
    path('gestao/utilizadores/<int:pk>/editar/', views.utilizador_editar, name='utilizador_editar'),
    path('gestao/utilizadores/<int:pk>/eliminar/', views.utilizador_eliminar, name='utilizador_eliminar'),
    
    # Gestão de Horários
    path('gestao/horarios/', views.horarios_gestao, name='horarios_gestao'),
    path('gestao/horarios/criar/', views.horario_criar, name='horario_criar'),
    path('gestao/horarios/<int:pk>/editar/', views.horario_editar, name='horario_editar'),
    path('gestao/horarios/<int:pk>/eliminar/', views.horario_eliminar, name='horario_eliminar'),
    path('gestao/horarios/<int:pk>/aprovar/', views.horario_aprovar, name='horario_aprovar'),
    path('gestao/horarios/ferias/criar/', views.ferias_criar, name='ferias_criar'),
    path('gestao/horarios/ferias/<int:pk>/eliminar/', views.ferias_eliminar, name='ferias_eliminar'),
    path('gestao/horarios/ferias/<int:pk>/aprovar/', views.ferias_aprovar, name='ferias_aprovar'),
    
    # Gestão de Categorias
    path('gestao/categorias-servicos/', views.categorias_servicos_gestao, name='categorias_servicos_gestao'),
    path('gestao/categorias-servicos/criar/', views.categoria_servico_criar, name='categoria_servico_criar'),
    path('gestao/categorias-servicos/<int:pk>/editar/', views.categoria_servico_editar, name='categoria_servico_editar'),
    path('gestao/categorias-servicos/<int:pk>/eliminar/', views.categoria_servico_eliminar, name='categoria_servico_eliminar'),
    
    # Contactos
    path('gestao/contactos/', views.contactos_lista, name='contactos_lista'),
    path('gestao/contactos/<int:pk>/', views.contacto_detalhe, name='contacto_detalhe'),
    path('gestao/contactos/<int:pk>/respondido/', views.contacto_marcar_respondido, name='contacto_marcar_respondido'),
    path('gestao/contactos/<int:pk>/eliminar/', views.contacto_eliminar, name='contacto_eliminar'),
    
    # Relatórios
    path('gestao/relatorios/', views.relatorios, name='relatorios'),
    # Bloqueios de horários
    path('gestao/bloqueios/', views.bloqueios_gestao, name='bloqueios_gestao'),
    path('gestao/bloqueios/criar/', views.bloqueio_criar, name='bloqueio_criar'),
    path('gestao/bloqueios/<int:pk>/eliminar/', views.bloqueio_eliminar, name='bloqueio_eliminar'),
]
