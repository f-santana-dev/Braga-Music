#-------------- forms.py------------- #                   

import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Cliente, ESTADOS_CHOICES

class ClienteCadastroForm(UserCreationForm):
    nome_completo = forms.CharField(max_length=255, label="Nome Completo")  # Adicionado campo "Nome Completo"
    email = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    cpf = forms.CharField(label="CPF", max_length=14, widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefone = forms.CharField(label="Telefone", max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cep = forms.CharField(label="CEP", max_length=9, widget=forms.TextInput(attrs={'class': 'form-control'}))
    endereco = forms.CharField(label="Endereço", max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero = forms.CharField(label="Número", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    complemento = forms.CharField(label="Complemento", max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bairro = forms.CharField(label="Bairro", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cidade = forms.CharField(label="Cidade", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    estado = forms.ChoiceField(label="Estado", choices=ESTADOS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Cliente
        fields = ["nome_completo", "email", "cpf", "telefone", "cep", "endereco", "numero", "complemento", "bairro", "cidade", "estado", "password1", "password2"]

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
            raise forms.ValidationError("Formato de CPF inválido. Use XXX.XXX.XXX-XX")
        return cpf


class LoginForm(forms.Form):
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))