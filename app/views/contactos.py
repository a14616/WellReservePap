"""Vistas de gestão de contactos."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .auth import admin_required
from ..models import Contacto


@admin_required
def contactos_lista(request):
	"""Lista de contactos"""
	contactos = Contacto.objects.all().order_by('-data_criacao')

	paginator = Paginator(contactos, 20)
	page = request.GET.get('page')
	contactos = paginator.get_page(page)

	return render(request, 'gestao/contactos_lista.html', {'contactos': contactos})


@admin_required
def contacto_detalhe(request, pk):
	"""Detalhe de um contacto"""
	contacto_obj = get_object_or_404(Contacto, pk=pk)

	if not contacto_obj.lida:
		contacto_obj.lida = True
		contacto_obj.save()

	return render(request, 'gestao/contacto_detalhe.html', {'contacto': contacto_obj})


@admin_required
def contacto_marcar_respondido(request, pk):
	"""Marcar contacto como respondido"""
	contacto_obj = get_object_or_404(Contacto, pk=pk)
	contacto_obj.respondida = True
	contacto_obj.save()
	messages.success(request, 'Contacto marcado como respondido.')
	return redirect('contactos_lista')


@admin_required
def contacto_eliminar(request, pk):
	"""Eliminar contacto"""
	contacto_obj = get_object_or_404(Contacto, pk=pk)

	if request.method == 'POST':
		contacto_obj.delete()
		messages.success(request, 'Contacto eliminado com sucesso!')
		return redirect('contactos_lista')

	return render(request, 'gestao/confirmar_eliminar.html', {
		'objeto': contacto_obj,
		'tipo': 'contacto',
		'voltar_url': 'contactos_lista'
	})
