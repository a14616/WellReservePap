"""
Formulários - WellReserve
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import (
    Reserva, Servico, HorarioFuncionario, Produto, 
    Encomenda, Contacto, CategoriaServico, CategoriaProduto,
    FeriasFuncionario
)
from datetime import date, datetime, timedelta

Utilizador = get_user_model()


class RegistoForm(UserCreationForm):
    """
    Formulário de registo de novos utilizadores (clientes)
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nome',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Apelido',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apelido'
        })
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Telefone'
        })
    )
    data_nascimento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = Utilizador
        fields = ['username', 'email', 'first_name', 'last_name', 'telefone', 'data_nascimento', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nome de utilizador'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Palavra-passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar palavra-passe'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.tipo = 'cliente'
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Formulário de login
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome de utilizador ou email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Palavra-passe'
        })
    )


class PerfilForm(forms.ModelForm):
    """
    Formulário de edição de perfil
    """
    class Meta:
        model = Utilizador
        fields = ['first_name', 'last_name', 'email', 'telefone', 'morada', 'data_nascimento', 'nif', 'foto']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'morada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }


class UtilizadorAdminForm(forms.ModelForm):
    """
    Formulário de gestão de utilizadores (admin)
    """
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Nova Palavra-passe',
        help_text='Deixe em branco para manter a palavra-passe atual'
    )
    
    class Meta:
        model = Utilizador
        fields = ['username', 'email', 'first_name', 'last_name', 'tipo', 'telefone', 'morada', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'morada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class CategoriaServicoForm(forms.ModelForm):
    """
    Formulário de categoria de serviço
    """
    class Meta:
        model = CategoriaServico
        fields = ['nome', 'descricao', 'icone', 'ordem', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-layer-group'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ServicoForm(forms.ModelForm):
    """
    Formulário de serviço
    """
    criar_horario_fixo = forms.BooleanField(
        required=False,
        label='Criar horário fixo para este serviço',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    horario_dia_semana = forms.ChoiceField(
        required=False,
        choices=HorarioFuncionario.DIAS_SEMANA,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    horario_hora_inicio = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    horario_hora_fim = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    horario_funcionario = forms.ModelChoiceField(
        required=False,
        queryset=Utilizador.objects.filter(tipo='funcionario', is_active=True).order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'categoria', 'duracao', 'preco', 'funcionarios', 
                  'imagem', 'capacidade_maxima', 'requer_prescricao', 'ativo', 'destaque', 'is_aula']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'duracao': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'max': 480}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'funcionarios': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'capacidade_maxima': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'requer_prescricao': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destaque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_aula': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class HorarioFuncionarioForm(forms.ModelForm):
    """
    Formulário de horário de funcionário
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_admin:
            self.fields['funcionario'].queryset = Utilizador.objects.filter(
                pk=self.user.pk,
                is_active=True
            )
            self.fields['funcionario'].initial = self.user
            self.fields['funcionario'].widget = forms.HiddenInput()
        elif self.user and self.user.is_admin:
            self.fields['funcionario'].queryset = Utilizador.objects.filter(
                tipo__in=['funcionario', 'recepcao'],
                is_active=True
            ).order_by('first_name', 'last_name', 'username')

    class Meta:
        model = HorarioFuncionario
        fields = ['funcionario', 'dia_semana', 'hora_inicio', 'hora_fim', 'data_inicio', 'data_fim', 'ativo']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fim = cleaned_data.get('hora_fim')
        
        if hora_inicio and hora_fim and hora_inicio >= hora_fim:
            raise forms.ValidationError('A hora de início deve ser anterior à hora de fim.')
        
        return cleaned_data


class FeriasFuncionarioForm(forms.ModelForm):
    """
    Formulário de férias de funcionário
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_admin:
            self.fields['funcionario'].queryset = Utilizador.objects.filter(
                pk=self.user.pk,
                is_active=True
            )
            self.fields['funcionario'].initial = self.user
            self.fields['funcionario'].widget = forms.HiddenInput()
        elif self.user and self.user.is_admin:
            self.fields['funcionario'].queryset = Utilizador.objects.filter(
                tipo__in=['funcionario', 'recepcao'],
                is_active=True
            ).order_by('first_name', 'last_name', 'username')

    class Meta:
        model = FeriasFuncionario
        fields = ['funcionario', 'data_inicio', 'data_fim', 'motivo']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim and data_inicio > data_fim:
            raise forms.ValidationError('A data de início deve ser anterior ou igual à data de fim.')
        
        return cleaned_data


class ReservaForm(forms.ModelForm):
    """
    Formulário de reserva (cliente)
    """
    class Meta:
        model = Reserva
        fields = ['servico', 'funcionario', 'data', 'hora', 'notas']
        widgets = {
            'servico': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.HiddenInput(),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações adicionais...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servico'].queryset = Servico.objects.filter(ativo=True)
        self.fields['funcionario'].queryset = Utilizador.objects.filter(tipo='funcionario', is_active=True)
        self.fields['funcionario'].required = False
        # `hora` ficará como HiddenInput — horários são selecionados via interface
        
        # Data mínima é amanhã
        self.fields['data'].widget.attrs['min'] = (date.today() + timedelta(days=1)).isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        servico = cleaned_data.get('servico')
        funcionario = cleaned_data.get('funcionario')
        data = cleaned_data.get('data')
        hora = cleaned_data.get('hora')

        if data and data <= date.today():
            self.add_error('data', 'A data deve ser posterior a hoje.')

        if not servico or not data or not hora:
            return cleaned_data

        funcionarios = [funcionario] if funcionario else list(
            servico.funcionarios.filter(is_active=True)
        )

        if not funcionarios:
            self.add_error('funcionario', 'Não existem profissionais disponíveis para este serviço.')
            return cleaned_data

        dia_semana = data.weekday()
        horario_valido = False

        for func in funcionarios:
            em_ferias = FeriasFuncionario.objects.filter(
                funcionario=func,
                data_inicio__lte=data,
                data_fim__gte=data,
                estado='aprovado'
            ).exists()
            if em_ferias:
                continue

            horarios_funcionario = HorarioFuncionario.objects.filter(
                funcionario=func,
                dia_semana=dia_semana,
                ativo=True,
                estado='aprovado'
            )

            inicio = datetime.combine(data, hora)

            # Se o serviço é uma aula e não existem horários aprovados para este dia,
            # permitir reserva ad-hoc (desde que não haja conflito).
            if servico.is_aula and not horarios_funcionario.exists():
                encaixa_horario = True
            else:
                encaixa_horario = False
                for horario in horarios_funcionario:
                    inicio_turno = datetime.combine(data, horario.hora_inicio)
                    fim_turno = datetime.combine(data, horario.hora_fim)
                    if inicio >= inicio_turno and (inicio + timedelta(minutes=servico.duracao)) <= fim_turno:
                        encaixa_horario = True
                        break
                if not encaixa_horario:
                    continue

            conflito = Reserva.objects.filter(
                funcionario=func,
                data=data,
                estado__in=['pendente', 'confirmada'],
                hora=hora,
            ).exists()

            if not conflito:
                horario_valido = True
                if not funcionario:
                    cleaned_data['funcionario'] = func
                break

        if not horario_valido:
            self.add_error('hora', 'Este horário já não está disponível. Escolha outro horário.')

        return cleaned_data


class ReservaAdminForm(forms.ModelForm):
    """
    Formulário de reserva (admin/receção/funcionário)
    """
    class Meta:
        model = Reserva
        fields = ['cliente', 'servico', 'funcionario', 'data', 'hora', 'estado', 'notas', 'notas_internas', 'preco_final']
        widgets = {
            'cliente': forms.HiddenInput(),  # Campo hidden - será preenchido pela busca JavaScript
            'servico': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notas_internas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preco_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Utilizador.objects.filter(tipo='cliente', is_active=True)
        self.fields['servico'].queryset = Servico.objects.filter(ativo=True)
        self.fields['funcionario'].queryset = Utilizador.objects.filter(tipo='funcionario', is_active=True)
        self.fields['cliente'].required = True  # Garantir que cliente é obrigatório
    
    def clean_cliente(self):
        cliente = self.cleaned_data.get('cliente')
        if not cliente:
            raise forms.ValidationError('Selecione um cliente.')
        return cliente


class CategoriaProdutoForm(forms.ModelForm):
    """
    Formulário de categoria de produto
    """
    class Meta:
        model = CategoriaProduto
        fields = ['nome', 'descricao', 'ordem', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProdutoForm(forms.ModelForm):
    """
    Formulário de produto
    """
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'categoria', 'preco', 'stock', 'imagem', 'ativo', 'destaque']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'destaque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EncomendaAdminForm(forms.ModelForm):
    """
    Formulário de encomenda (admin)
    """
    class Meta:
        model = Encomenda
        fields = ['cliente', 'estado', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CheckoutEncomendaForm(forms.Form):
    """
    Formulário de checkout com faturação e pagamento fictício
    """
    faturacao_nome = forms.CharField(
        label='Nome de Faturação',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    faturacao_email = forms.EmailField(
        label='Email de Faturação',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    faturacao_nif = forms.CharField(
        label='NIF',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    faturacao_morada = forms.CharField(
        label='Morada de Faturação',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    entrega_morada_igual_faturacao = forms.BooleanField(
        label='A morada de entrega é igual à de faturação',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    entrega_morada = forms.CharField(
        label='Morada de Entrega',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    metodo_pagamento = forms.ChoiceField(
        label='Método de Pagamento',
        choices=Encomenda.METODO_PAGAMENTO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('entrega_morada_igual_faturacao'):
            cleaned_data['entrega_morada'] = cleaned_data.get('faturacao_morada', '')
        elif not cleaned_data.get('entrega_morada'):
            self.add_error('entrega_morada', 'Indique a morada de entrega ou marque que é igual à de faturação.')
        return cleaned_data

    notas = forms.CharField(
        label='Notas',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class ContactoForm(forms.ModelForm):
    """
    Formulário de contacto
    """
    class Meta:
        model = Contacto
        fields = ['nome', 'email', 'telefone', 'assunto', 'mensagem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'O seu nome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'O seu email'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'O seu telefone (opcional)'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assunto'}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'A sua mensagem...'}),
        }


class PesquisaReservaForm(forms.Form):
    """
    Formulário de pesquisa de reservas
    """
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Início'
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Fim'
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(Reserva.ESTADO_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    servico = forms.ModelChoiceField(
        required=False,
        queryset=Servico.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Serviço',
        empty_label='Todos'
    )
