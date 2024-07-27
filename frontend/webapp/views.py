from django.shortcuts import render


def offline(request):
    '''Serve PWA offline page (attempts to reconnect every 15 seconds)'''
    return render(request, 'webapp/offline.html')
