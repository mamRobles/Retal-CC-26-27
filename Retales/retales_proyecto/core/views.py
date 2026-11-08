from django.http import HttpResponse
from django.shortcuts import render
def health(request):
    return HttpResponse('ok')
def base_view(request):
    return render(request, 'base.html')