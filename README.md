 WellReserve

 Descrição

O WellReserve é uma aplicação web desenvolvida em Python utilizando a framework Django.

O projeto foi desenvolvido no âmbito da Prova de Aptidão Profissional (PAP) do Curso Profissional de Programador de Informática da Escola Profissional Oficina.

A aplicação permite gerir reservas, serviços, funcionários, clientes, produtos e encomendas através de uma plataforma centralizada, com diferentes níveis de acesso consoante o tipo de utilizador.



 Funcionalidades

 Gestão de Utilizadores

* Registo e autenticação de utilizadores
* Gestão de perfis
* Diferentes níveis de acesso (Administrador, Funcionário e Cliente)

 Gestão de Serviços

* Criação e edição de serviços
* Organização por categorias
* Definição de duração e preço
* Associação de funcionários aos serviços

 Reservas

* Criação de reservas
* Consulta de disponibilidade
* Histórico de reservas
* Cancelamento de reservas

 Gestão de Horários

* Definição de horários de trabalho
* Gestão de férias e ausências
* Controlo de disponibilidade dos funcionários

 Produtos e Encomendas

* Catálogo de produtos
* Gestão de stock
* Criação de encomendas
* Consulta do histórico de encomendas

 Contactos

* Envio de mensagens através de formulário de contacto
* Gestão das mensagens recebidas



 Tecnologias Utilizadas

* Python
* Django
* HTML
* CSS
* JavaScript
* Bootstrap
* SQLite


 Estrutura do Projeto

* `WellReserve/` – Configuração principal do projeto Django
* `app/` – Aplicação principal
* `templates/` – Páginas HTML
* `static/` – Ficheiros CSS, JavaScript e imagens
* `media/` – Ficheiros enviados pelos utilizadores



 Instalação

Criar ambiente virtual:

```bash
python -m venv venv
```

Ativar ambiente virtual:

```bash
venv\Scripts\activate
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar migrações:

```bash
python manage.py migrate
```

Criar administrador:

```bash
python manage.py createsuperuser
```

Executar a aplicação:

```bash
python manage.py runserver
```

---

 Requisitos

* Python 3.10 ou superior
* Ligação à Internet
* Navegador Web atualizado

---

 Autor

Gabriel Viana

N.º 14616

Turma 12P

Curso Profissional de Programador de Informática

Escola Profissional Oficina

Orientador: David Cerqueira


 Finalidade

Este projeto foi desenvolvido exclusivamente para fins académicos no âmbito da Prova de Aptidão Profissional (PAP).
