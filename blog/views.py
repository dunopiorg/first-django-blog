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
from .controllers import RecordApp, GspreadTemplate


# region [API]
@csrf_exempt
def get_article(request):
    if request.method == "GET" or request.method == "OPTIONS":
        lab2ai_conn = Lab2AIConnector()
        data = request.GET.get('game_id', None)
        if data:
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
            article_dict['version'] = counter + 1

            lab2ai_conn.insert_history(article_dict, counter)
            response = JsonResponse({'status': 'OK', 'message': counter})
        else:
            response = JsonResponse({'status': 'FAIL', 'message': 'Not exist keys'})

    return response


@csrf_exempt
def get_article_v2(request):
    if request.method == "GET" or request.method == "OPTIONS":
        response_game_id = request.GET.get('game_id', None)
        if response_game_id:
            args, lab64_status = get_article_from_lab64_v2(response_game_id)

            if args['status'] == "OK":
                article_dict = set_article_v2_to_db(args)
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

    try:
        game_id = data['game_id']
        le_id = data['le_id']
        gyear = data['gyear']
        title = data['title'].replace("\"", "'")
        article = data['article'].replace("\"", "'")
        serial = data['serial']
        status = data['status']

        article_dict = {}

        if game_id == '' or le_id == '' or gyear == '':
            raise Exception('Key Value is Empty')

        article_dict['game_id'] = game_id
        article_dict['le_id'] = le_id
        article_dict['gyear'] = gyear
        article_dict['status'] = status
        article_dict['serial'] = serial
        article_dict['title'] = title
        article_dict['article'] = article
        article_dict['created_at'] = data['created_at']

        counter = lab2ai_conn.select_count(article_dict['game_id'], article_dict['gyear'])[0]
        article_dict['version'] = counter+1

        lab2ai_conn.insert_history(article_dict, counter)
        response = JsonResponse({'status': 'OK', 'message': counter}, status=200)
    except Exception as ex:
        return JsonResponse({'status': 'FAIL', 'message': ex}, status=300)
    return response


@csrf_exempt
def get_article_v2_test(request, game_id):
    if request.method == "GET" or request.method == "OPTIONS":
        args, lab64_status = get_article_from_lab64_v2(game_id)

        game_id = args['game_id']
        title = args['article']['title']
        article = args['article']['body']
        info = args['info']
        article_dict = get_article_text_dict(info)
        article_text = "\n\n".join(article_dict['article'])
        team_info = RecordApp().get_paragraph(game_id)

        context = {'title': title, 'article': article_text, 'team': team_info}
        return render(request, 'blog/team_info.html', context)
# endregion [API]


# region 임시 테스트
@csrf_exempt
def test(request):
    record_app = RecordApp()
    args = record_app.get_paragraph()
    context = {'args': args}
    return render(request, 'blog/team_info.html', context)


@csrf_exempt
def test_2(request, game_id):
    result_list = []
    args, lab64_status = get_article_from_lab64_v2(game_id)
    title = args['article']['title']
    article = args['article']['body']
    info = args['info']
    pitcher_dict, hitter_list = get_player_info_test(info)
    record_app = RecordApp()

    # for code, name in pitcher_dict.items():
    #     result_list.append(record_app.get_player_event_dict(game_id, pitcher_code=code))

    for h_dict in hitter_list:
        result_list.append(record_app.get_player_event_dict(game_id, player_name=h_dict['hitter_name'], hitter_code=h_dict['hitter_code']))

    context = {'title': title, 'article': article, 'info': result_list}
    return render(request, 'blog/test_player_info.html', context)
# endregion 임시 테스트


@csrf_exempt
def template_viewer(request, db_name=None):
    worksheets = get_template_table_list()
    table_list = [d.title for d in worksheets]
    context = {"tables": table_list}

    if db_name is not None:
        worksheet_index = table_list.index(db_name)
        list_of_hash = worksheets[worksheet_index].get_all_records()
        if list_of_hash:
            GspreadTemplate().set_rds_template_from_gspread(db_name, list_of_hash)

    return render(request, 'blog/template_db_setting.html', context)


# region [LAB64]
def get_article_from_lab64(game_id):
    lab64_url = cfg.lab64_url
    url_form = "{}{}".format(lab64_url, game_id)
    get_response = get(url_form)

    return get_response.json(), get_response.status_code


def get_article_from_lab64_v2(game_id):
    lab64_url = cfg.lab64_v2_url
    url_form = "{}{}".format(lab64_url, game_id)
    get_response = get(url_form)

    return get_response.json(), get_response.status_code


def call_refresh_game_lab64(game_id):
    lab64_url = cfg.lab64_admin_url
    url_form = "{0}{1}/refresh".format(lab64_url, game_id)
    get_response = get(url_form)

    return get_response


def get_article_text_dict(info_list):
    result_dict = {}
    article_list = []
    for info_dict in info_list:
        if info_dict['p_num'] == 0:
            result_dict['title'] = info_dict['text']
        else:
            article_list.append(info_dict['text'])

    result_dict['article'] = article_list
    return result_dict
# endregion [LAB64]


# region Blog
def post_list(request):
    return render(request, 'blog/post_list.html', {})


def home(request):
    gameinfo_dict_list = RecordApp().get_gameinfo_dict_list()
    args = {'gameinfo': gameinfo_dict_list}
    return render(request, 'blog/home.html', args)


def futures(request, game_id):
    article_dict_v1 = RecordApp().get_article(game_id)
    article_dict_v2 = RecordApp().get_article_v2(game_id)

    # Lab64 요청
    if article_dict_v1 is None:
        call_refresh_game_lab64(game_id)
        args, lab64_status = get_article_from_lab64(game_id)
        if args['success']:
            article_dict_v1 = set_article_v1_to_db(args)
        else:
            return render(request, 'blog/futures_article.html', {'status': 'ERROR', 'error': args['status']})
    else:
        article_dict_v1 = article_dict_v1[0]

    if article_dict_v2 is None:
        args_v2, lab64_status_v2 = get_article_from_lab64_v2(game_id)

        if args_v2['success']:
            article_dict_v2 = set_article_v2_to_db(args_v2)
        else:
            return render(request, 'blog/futures_article.html', {'status': 'ERROR', 'error': args_v2['status']})
    else:
        article_dict_v2 = article_dict_v2[0]

    title_v1 = article_dict_v1['title']
    article_text_v1 = article_dict_v1['article']
    article_list_v1 = article_text_v1.split("\n\n")

    title_v2 = article_dict_v2['title']
    article_text_v2 = article_dict_v2['article']
    article_list_v2 = article_text_v2.split("\n\n")

    result_article = {'game_id': game_id, 'status': 'OK',
                      'title_v1': title_v1, 'article_text_v1': article_list_v1,
                      'title_v2': title_v2, 'article_text_v2': article_list_v2, }
    return render(request, 'blog/futures_article.html', result_article)


def refresh_futures(request, game_id):
    # Lab64 요청
    article_dict = {}

    title = article_dict['title']
    article_text = article_dict['article']
    article_list = article_text.split("\n\n")

    result_article = {'title': title, 'article_text': article_list, 'game_id': game_id}
    return render(request, 'blog/futures_article.html', result_article)


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


# region [ETC FUNCTIONS]
def set_article_v2_to_db(args):
    article_dict = {}
    lab2ai_conn = Lab2AIConnector()

    article_dict['game_id'] = args['game_id']
    article_dict['status'] = args['status']
    article_dict['le_id'] = args['le_id']
    article_dict['gyear'] = args['gyear']
    article_dict['serial'] = args['serial']

    info = args['info']
    article_args_dict = get_article_text_dict(info)
    team_text = RecordApp().get_paragraph(article_dict['game_id'])

    article_dict['title'] = article_args_dict['title']
    article_args_dict['article'].append(team_text)
    article_text = "\n\n".join(article_args_dict['article'])
    article_dict['article'] = article_text

    article_dict['created_at'] = change_date_array(args['created_at'])
    lab2ai_conn.insert_article_v2(article_dict)

    return article_dict


def set_article_v1_to_db(args):
    article_dict = {}
    lab2ai_conn = Lab2AIConnector()

    game_id = args['game_id']
    status = args['status']
    le_id = args['le_id']
    gyear = args['gyear']
    serial = args['serial']
    title = args['article']['title']
    article = args['article']['body']
    args_created_at = change_date_array(args['created_at'])

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

    return article_dict


def get_template_table_list():
    return GspreadTemplate().get_template_tab_list()


def change_date_array(date_time):
    d = date_time
    result = datetime.strptime(d, "%Y-%d-%m %X").strftime("%Y-%m-%d %X")
    return result


def get_player_info_test(data_list):
    pitcher_dict = {}
    hitter_list = []
    for info_d in data_list:
        if info_d["info"]:
            info_detail = info_d["info"]
            inn = info_detail["inning"]
            tb = info_detail["tb"]
            for hitter_event in info_detail["hitter_events"]:
                for hitter_scene in hitter_event["score_scenes"]:
                    for d in hitter_scene['hitter_or_runner']:
                        hitter_code = d["pcode"]
                        hitter_name = d["name"]
                        hitter_list.append({'hitter_code': hitter_code, 'hitter_name': hitter_name, "inning": inn, "tb": tb})
                    pitcher_code = hitter_scene["pitcher"]["pcode"]
                    pitcher_name = hitter_scene["pitcher"]["name"]
                    if pitcher_code not in pitcher_dict:
                        pitcher_dict[pitcher_code] = pitcher_name

    return pitcher_dict, hitter_list
# endregion [ETC FUNCTIONS]
