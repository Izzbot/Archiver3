import requests, os, sys, boto, time
sys.path.insert(0, '/home/ubuntu/lab3')
from mysite import creds
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import URL
from .forms import URLForm
from .serializers import URLSerializer

from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.conf import settings
from selenium import webdriver
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from ratelimit.decorators import ratelimit

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='accounts/login')
def url_list(request):
    if not request.user.is_authenticated():
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    else:
        urls = URL.objects.order_by('collected_date')
        return render(request, 'archive/url_list.html', {'urls': urls})

@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='../../accounts/login')
def url_detail(request, pk):
    if not request.user.is_authenticated():
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    else:
        url = get_object_or_404(URL, pk=pk)
        return render(request, 'archive/url_detail.html', {'url': url})

@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='../../accounts/login')
def url_new(request):
    if not request.user.is_authenticated():
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    else:
        if request.method == "POST":
            form = URLForm(request.POST)
            if form.is_valid():
                url = form.save(commit=False)
                url.collected_date = timezone.now()

                # connect up and fetch the website
                try:
                    req = requests.request('GET', url.init_url)
                except:
                    # if the connection breaks
                    url.status = '404'
                    url.title = ''
                    url.snapshot_url = ''
                    url.final_url = url.init_url
                    url.save()
                    url = get_object_or_404(URL, pk=url.pk)
                    return redirect('archive.views.url_detail', pk=url.pk)

                # assign data
                url.status = req.status_code
                url.final_url = req.url

                # Use bs4 to parse the data
                soup = BeautifulSoup(req.text)
                if soup is not None:
                    url.title = soup.title.string
                else:
                    url.title = ''

                # Use selenium to grab image
                try:
                    # get the screenshot
                    driver = webdriver.PhantomJS(service_log_path = os.path.devnull)
                    driver.set_window_size(1024, 768)
                    driver.get(url.final_url)
                    url.save()
                    nameFile = str(url.id) + '.png'
                    driver.save_screenshot('/tmp/%s' % nameFile)

                    # get the S3 connection to save screenshot
                    conn = S3Connection(creds.AWS_ACCESS_KEY_ID, creds.AWS_SECRET_ACCESS_KEY)
                    zeBucket = conn.get_bucket('izzy-lab3')
                    zeKey = Key(zeBucket)
                    zeKey.key = 'screenshots/' + nameFile
                    zeKey.set_contents_from_filename('/tmp/%s' % nameFile)
                    zeKey.make_public()

                    # clean up and set the url
                    os.remove('/tmp/%s' % nameFile)
                    driver.quit()
                    url.snapshot_url = 'https://s3.amazonaws.com/izzy-lab3/screenshots/' + nameFile
                except:
                    url.snapshot_url = ''

                url.save()
                url = get_object_or_404(URL, pk=url.pk)
                return redirect('archive.views.url_detail', pk=url.pk)
        else:
            form = URLForm()
        return render(request, 'archive/url_new.html', {'form': form})

@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='../../../accounts/login')
def url_delete(request, pk):
    if not request.user.is_authenticated():
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    else:
        url = get_object_or_404(URL, pk=pk)
        url.delete()
        return redirect('archive.views.url_list')

## Start of API Views
## It gets crazy here!

@ratelimit(key='ip', rate='10/m', block=True)
@api_view(['GET', 'DELETE'])
def api_url_detail(request, pk, format=None):
    try:
        zeURL = URL.objects.get(pk=pk)
    except URL.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = URLSerializer(zeURL)
        return Response(serializer.data)
    elif request.method == 'DELETE':

        conn = S3Connection(creds.AWS_ACCESS_KEY_ID, creds.AWS_SECRET_ACCESS_KEY)
        zeBucket = conn.get_bucket('izzy-lab3')
        zeKey = Key(zeBucket)
        zeS3 = zeURL.snapshot_url.split("/")
        nameFile = zeS3.pop()
        zeKey.key = 'screenshots/' + nameFile
        zeBucket.delete_key(zeKey)
        zeURL.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@ratelimit(key='ip', rate='10/m', block=True)
@api_view(['GET', 'POST'])
def api_url_list(request, format=None):
    if request.method == 'GET':
        urls = URL.objects.all()
        serializer = URLSerializer(urls, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data

        # assign data
        data['collected_date'] = timezone.now()
        data['snapshot_url'] = 'http://test.com'

        # connect up and fetch the website
        try:
            req = requests.request('GET', data['init_url'])
        except:
            # if the connection breaks
            return Response('bad connection', status=status.HTTP_400_BAD_REQUEST)

        # assign request data
        data['final_url'] = req.url
        data['status'] = req.status_code

        # Use bs4 to parse the data
        soup = BeautifulSoup(req.text)
        if soup is not None:
            data['title'] = soup.title.string
        else:
            data['title'] = ''

        # Use selenium to grab image
        nameFile = data['collected_date'].strftime('%Y-%m-%s-%H-%M-%S') + '.png'

        try:
            # get the screenshot
            driver = webdriver.PhantomJS(service_log_path = os.path.devnull)
            driver.set_window_size(1024, 768)
            driver.get(data['final_url'])
            driver.save_screenshot('/tmp/%s' % nameFile)

            # get the S3 connection to save screenshot
            conn = S3Connection(creds.AWS_ACCESS_KEY_ID, creds.AWS_SECRET_ACCESS_KEY)
            zeBucket = conn.get_bucket('izzy-lab3')
            zeKey = Key(zeBucket)
            zeKey.key = 'screenshots/' + nameFile
            zeKey.set_contents_from_filename('/tmp/%s' % nameFile)
            zeKey.make_public()

            # clean up and set the url
            os.remove('/tmp/%s' % nameFile)
            driver.quit()
            data['snapshot_url'] = 'https://s3.amazonaws.com/izzy-lab3/screenshots/' + nameFile
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer = URLSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@ratelimit(key='ip', rate='10/m', block=True)
@api_view(['GET'])
def api_url_recapture(request, pk, format=None):
    if request.method == 'GET':

        try:
            zeURL = URL.objects.get(pk=pk)
        except URL.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Use selenium to grab image
        try:
            zeS3 = zeURL.snapshot_url.split("/")
            oldFile = zeS3.pop()
            nameFile = str(zeURL.id) + '.png'

            conn = S3Connection(creds.AWS_ACCESS_KEY_ID, creds.AWS_SECRET_ACCESS_KEY)
            # get the S3 connection to save screenshot
            zeBucket = conn.get_bucket('izzy-lab3')
            zeKey = Key(zeBucket)

            # delete old file
            zeKey.key = 'screenshots/' + oldFile
            zeBucket.delete_key(zeKey)

            # get the screenshot
            driver = webdriver.PhantomJS(service_log_path = os.path.devnull)
            driver.set_window_size(1024, 768)
            driver.get(zeURL.final_url)
            driver.save_screenshot('/tmp/%s' % nameFile)

            # upload new file
            zeKey.key = 'screenshots/' + nameFile
            zeKey.set_contents_from_filename('/tmp/%s' % nameFile)
            zeKey.make_public()

            # clean up and set the url
            os.remove('/tmp/%s' % nameFile)
            driver.quit()
            zeURL.snapshot_url = 'https://s3.amazonaws.com/izzy-lab3/screenshots/' + nameFile
        except:
            return Response(str(zeURL.snapshot_url), status=status.HTTP_400_BAD_REQUEST)

        serializer = URLSerializer(zeURL)
        return Response(serializer.data)
    return Response(status=status.HTTP_400_BAD_REQUEST)

