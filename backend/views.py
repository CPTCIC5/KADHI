from django.shortcuts import render
#from django.contrib.auth.views import PasswordResetView

def page_not_found_view(request, exception):
    return render(request, '404page.html', status=404)