from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages

def get_index(request):

    return render(request, 'index.html')


# Create your views here.
