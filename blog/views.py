import json
from datetime import datetime
from requests import get
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from blog.forms import (
    RegistrationForm, 
    EditProfileForm
)
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

# Create your views here.
from .models import Post, Lab2AIConnector
from . import config as cfg
from .controllers import RecordApp


# region Article
@csrf_exempt
def get_article(request):
    if request.method == "GET" or request.method == "OPTIONS":
        lab2ai_conn = Lab2AIConnector()
        data = request.GET.get('game_id', None)
        if data:
            # data = json.load(request.body.decode("utf-8")) #json.loads(request.body.decode("utf-8"))
            # args, lab64_status = get_article_from_lab64(data['game_id'])
            args, lab64_status = get_article_from_lab64(data)
            
            game_id = args['game_id']
            status = args['status']
            le_id = args['le_id']
            gyear = args['gyear']
            serial = args['serial']
            title = args['article']['title']
            article = args['article']['body']
            args_created_at = change_date_array(args['created_at'])
            article_dict = {}

            if status == "OK":
                article_dict['game_id'] = game_id
                article_dict['status'] = status
                article_dict['le_id'] = le_id
                article_dict['gyear'] = gyear
                article_dict['serial'] = serial
                article_dict['title'] = title
                article_dict['article'] = article
                article_dict['created_at'] = args_created_at
                lab2ai_conn.insert_article(article_dict)
                response = JsonResponse(article_dict)
            else:
                response = JsonResponse({'status': 'FAIL', 'message': 'There are some missing data'})
        else:
            response = JsonResponse({'status': 'FAIL', 'message': 'game_id does not exist'})
    elif request.method == "POST":
        lab2ai_conn = Lab2AIConnector()
        data = json.loads(request.body.decode("utf-8"))

        game_id = data['game_id']
        le_id = data['le_id']
        gyear = data['gyear']
        title = data['title'].replace("\"", "'")
        article = data['article'].replace("\"", "'")
        article_dict = {}

        if game_id and le_id and gyear:
            article_dict['game_id'] = game_id
            article_dict['le_id'] = le_id
            article_dict['gyear'] = gyear
            article_dict['status'] = data['status']
            article_dict['serial'] = data['serial']
            article_dict['title'] = title
            article_dict['article'] = article
            article_dict['created_at'] = data['created_at']

            counter = lab2ai_conn.select_count(article_dict['game_id'], article_dict['gyear'])[0]
            article_dict['version'] = counter+1

            lab2ai_conn.insert_history(article_dict, counter)
            response = JsonResponse({'status': 'OK', 'message': counter})
        else:
            response = JsonResponse({'status': 'FAIL', 'message': 'Not exist keys'})

    return response


@csrf_exempt
def get_article_v2(request):
    if request.method == "GET" or request.method == "OPTIONS":
        lab2ai_conn = Lab2AIConnector()
        response_game_id = request.GET.get('game_id', None)
        if response_game_id:
            args, lab64_status = get_article_from_lab64_v2(response_game_id)

            game_id = args['game_id']
            status = args['status']
            le_id = args['le_id']
            gyear = args['gyear']
            serial = args['serial']
            title = args['article']['title']
            article = args['article']['body']
            args_created_at = change_date_array(args['created_at'])
            article_dict = {}

            if status == "OK":
                article_dict['game_id'] = game_id
                article_dict['status'] = status
                article_dict['le_id'] = le_id
                article_dict['gyear'] = gyear
                article_dict['serial'] = serial
                article_dict['title'] = title
                article_dict['article'] = article
                article_dict['created_at'] = args_created_at
                lab2ai_conn.insert_article(article_dict)
                response = JsonResponse(article_dict)
            else:
                response = JsonResponse({'status': 'FAIL', 'message': 'There are some missing data'})
        else:
            response = JsonResponse({'status': 'FAIL', 'message': 'game_id does not exist'})
    elif request.method == "POST":
        lab2ai_conn = Lab2AIConnector()
        data = json.loads(request.body.decode("utf-8"))

        game_id = data['game_id']
        le_id = data['le_id']
        gyear = data['gyear']
        title = data['title'].replace("\"", "'")
        article = data['article'].replace("\"", "'")
        article_dict = {}

        if game_id and le_id and gyear:
            article_dict['game_id'] = game_id
            article_dict['le_id'] = le_id
            article_dict['gyear'] = gyear
            article_dict['status'] = data['status']
            article_dict['serial'] = data['serial']
            article_dict['title'] = title
            article_dict['article'] = article
            article_dict['created_at'] = data['created_at']

            counter = lab2ai_conn.select_count(article_dict['game_id'], article_dict['gyear'])[0]
            article_dict['version'] = counter + 1

            lab2ai_conn.insert_history(article_dict, counter)
            response = JsonResponse({'status': 'OK', 'message': counter})
        else:
            response = JsonResponse({'status': 'FAIL', 'message': 'Not exist keys'})

    return response


@csrf_exempt
def set_article(request):
    lab2ai_conn = Lab2AIConnector()
    data = json.loads(request.body.decode("utf-8"))
    
    game_id = data['game_id']
    le_id = data['le_id']
    gyear = data['gyear']
    title = data['title'].replace("\"", "'")
    article = data['article'].replace("\"", "'")
    article_dict = {}

    if game_id and le_id and gyear:
        article_dict['game_id'] = game_id
        article_dict['le_id'] = le_id
        article_dict['gyear'] = gyear
        article_dict['status'] = data['status']
        article_dict['serial'] = data['serial']
        article_dict['title'] = title
        article_dict['article'] = article
        article_dict['created_at'] = data['created_at']

        counter = lab2ai_conn.select_count(article_dict['game_id'], article_dict['gyear'])[0]
        article_dict['version'] = counter+1

        lab2ai_conn.insert_history(article_dict, counter)
        response = JsonResponse({'status': 'OK', 'message': counter}, status=200)
    else:
        response = JsonResponse({'status':'FAIL', 'message': 'Not exist keys'}, status=300)
    return response
# endregion Article


@csrf_exempt
def test(request):
    record_app = RecordApp()
    # data = json.loads(request.body.decode('utf-8'))
    # game_id = data['game_id']
    # hitter = data['hitter']
    args = record_app.test_get_team()
    # player_result = record_app.get_player_event_dict(game_id, hitter_code=hitter)
    context = {'args': args}
    # response = JsonResponse(result_dict, status=200)
    # render(request, 'blog/test_team_info.html', player_result)
    return render(request, 'blog/test_team_info.html', context)


@csrf_exempt
def set_rds_database(request):
    record_app = RecordApp()
    record_app.set_rds_database_from_gsheet()
    response = JsonResponse({'status': 'OK', 'message': 'GOOD'}, status=200)
    return response


def get_article_from_lab64(game_id):
    lab64_url = cfg.lab64_url
    url_form = "{}{}".format(lab64_url, game_id)
    get_response = get(url_form)

    return get_response.json(), get_response.status_code


def get_article_from_lab64_v2(game_id):
    lab64_url = cfg.lab64_v2_url_url
    url_form = "{}{}".format(lab64_url, game_id)
    get_response = get(url_form)

    return get_response.json(), get_response.status_code


# region Blog
def post_list(request):
    return render(request, 'blog/post_list.html', {})


def home(request):
    numbers = [1, 2, 3, 4, 5]
    name = 'Robot Write An Article'
    
    args = {'siteName': name, 'numbers': numbers}
    return render(request, 'blog/home.html', args)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/blog/home')
    else:
        form = RegistrationForm()
        
        args = {'form': form}
        return render(request, 'blog/reg_form.html', args)


@login_required
def view_profile(request):
    args = {'user': request.user}
    return render(request, 'blog/profile.html', args)


@login_required
def edit_profile(request):  
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        
        if form.is_valid():
            form.save()
            return redirect('/blog/profile')
    else:
        form = EditProfileForm(instance=request.user)
        args = {'form': form}
        return render(request, 'blog/edit_profile.html', args)


@login_required
def change_password(request):  
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)
        
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect('/blog/profile')
        else:
            return redirect('/blog/change-password')
    else:
        form = PasswordChangeForm(user=request.user)
        args = {'form': form}
        return render(request, 'blog/change_password.html', args)
# endregion Blog


def change_date_array(date_time):
    d = date_time
    result = datetime.strptime(d, "%Y-%d-%m %X").strftime("%Y-%m-%d %X")
    return result
