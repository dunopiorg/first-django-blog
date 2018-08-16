from datetime import datetime
from .models import Lab2AIConnector
from .lib.template_maker import Template
from .lib.records import Records
from .lib import gsheet_conn
from . import config as cfg
import pandas as pd
from collections import OrderedDict


class RecordApp(object):
    def __init__(self):
        self.lab2ai_conn = Lab2AIConnector()
        self.record = Records()
        self.template = Template()

    # region [TEAM EVENT]
    def get_team_paragraph(self, win_team, loss_team, game_id):
        data_dict = {}
        # data_dict = {'승리팀': self.record.MINOR_TEAM_NAME[win_team], '패배팀': self.record.MINOR_TEAM_NAME[loss_team]}
        win_team_data = self.record.get_team_win_record(win_team, game_id)
        if win_team_data:
            _win_team = self.get_variable_dict(win_team_data)
            data_dict['승리팀'] = _win_team
            # sentence_list.extend(win_team_data)

        loss_team_data = self.record.get_team_loss_record(loss_team, game_id)
        if loss_team_data:
            _loss_team = self.get_variable_dict(loss_team_data)
            data_dict['패배팀'] = _loss_team
            # sentence_list.extend(loss_team_data)

        versus_team_data = self.record.get_team_versus_record(win_team, loss_team, game_id)
        if versus_team_data:
            _versus_team = self.get_variable_dict(versus_team_data)
            data_dict['상대전적'] = _versus_team
            # sentence_list.extend(versus_team_data)

        # result_sentence = self.template.get_team_sentence_list(sentence_list)
        result_sentence = self.template.get_sentence_list(data_dict, cfg.TABLE_TEAM_SENTENCE)
        df_result_sentence = pd.DataFrame(result_sentence)
        if df_result_sentence.empty:
            return ''
        result_list = self.template.get_team_paragraph(df_result_sentence, data_dict)

        return result_list

    def get_paragraph(self, game_id):
        df_all_score = self.lab2ai_conn.get_test_team_scores(game_id)
        team_score = df_all_score.iloc[0]
        t_socre = team_score['TPOINT']
        b_socre = team_score['BPOINT']

        if t_socre > b_socre:
            win_team = game_id[8:10]
            loss_team = game_id[10:12]
        elif t_socre < b_socre:
            loss_team = game_id[8:10]
            win_team = game_id[10:12]
        else:
            return ''

        result_list = self.get_team_paragraph(win_team, loss_team, game_id)
        result_list = [d for d in result_list if d]
        result = ' '.join(result_list)

        return result
    # endregion [TEAM EVENT]

    # region [HITTER EVENT]
    def get_final_hit_event(self, game_id):
        final_hit_dict = self.record.get_hitter_final_hit(game_id)
        _final_hit = self.get_variable_dict(final_hit_dict)
        data_dict = {'결승타': _final_hit}
        return data_dict

    def get_player_event_dict(self, game_id, player_name=None, hitter_code=None, pitcher_code=None):
        result_list = []
        if hitter_code:
            # hitter
            result_list.append(self.record.get_hitter_n_continue_record(hitter_code))
            result_list.append(self.record.get_hitter_prev_record(hitter_code))
            result_list.append(self.record.get_hitter_first_hr(hitter_code, game_id))
        else:
            # pitcher
            result_list.append(self.record.get_pitcher_total_record(pitcher_code))
            result_list.append(self.record.get_pitcher_how_long_days(pitcher_code))
            result_list.append(self.record.get_pitcher_gamecontapp(pitcher_code, game_id))
            # result_list.append(self.record.get_pitcher_how_many_games(pitcher_code))
            result_list.append(self.record.get_pitcher_season_record(pitcher_code))
        return {'game_id': game_id, 'player_records': result_list, 'player_name': player_name}

    def get_hitter_event(self, game_id, hitter_code):
        data_dict = self.record.get_hitter_total_record(game_id, hitter_code)
        n_countinue_dict, n_last_dict = self.record.get_hitter_n_continue_record(game_id, hitter_code)
        df_person = self.lab2ai_conn.get_person_info(hitter_code)
        s_person = df_person.iloc[0]
        hitter_name = s_person['NAME']

        data_dict.update({'이름': hitter_name})
        data_dict.update({'n경기_연속': self.get_variable_dict(n_countinue_dict)})
        data_dict.update({'n경기_만에': self.get_variable_dict(n_last_dict)})

        hitter_info = self.get_variable_dict(data_dict)
        return hitter_info

    # endregion [HITTER EVENT]

    # region [PITCHER EVENT]
    def get_pitcher_event(self, game_id, pitcher_code):
        data_dict = self.record.get_pitcher_total_record(game_id, pitcher_code)
        n_countinue_dict, n_last_dict = self.record.get_pitcher_n_continue_record(game_id, pitcher_code)
        df_person = self.lab2ai_conn.get_person_info(pitcher_code)
        s_person = df_person.iloc[0]
        pitcher_name = s_person['NAME']

        data_dict.update({'이름': pitcher_name})
        data_dict.update({'n경기_연속': self.get_variable_dict(n_countinue_dict)})
        data_dict.update({'n경기_만에': self.get_variable_dict(n_last_dict)})

        pitcher_info = self.get_variable_dict(data_dict)
        return pitcher_info
    # endregion [PITCHER EVENT]

    # region [ARTICLE CONTROL FUNCTION]
    @classmethod
    def set_article_v1_to_db(cls, args):
        article_dict = {}
        lab2ai_conn = Lab2AIConnector()

        game_id = args['game_id']
        status = args['status']
        le_id = args['le_id']
        gyear = args['gyear']
        serial = args['serial']
        title = args['article']['title']
        article = args['article']['body']
        args_created_at = cls.change_date_array(args['created_at'])

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

    def set_article_v2_to_db(self, args):
        article_dict = {}
        lab2ai_conn = Lab2AIConnector()

        article_dict['game_id'] = args['game_id']
        article_dict['status'] = args['status']
        article_dict['le_id'] = args['le_id']
        article_dict['gyear'] = args['gyear']
        article_dict['serial'] = args['serial']

        info = args['info']
        article_args_dict = self.get_article_text_dict(info, game_id=article_dict['game_id'])
        team_text = RecordApp().get_paragraph(article_dict['game_id'])

        article_dict['title'] = article_args_dict['title']
        article_args_dict['article'].append(team_text)
        article_text = "\n\n".join(article_args_dict['article'])

        df_gameinfo = lab2ai_conn.get_gameinfo(article_dict['game_id'])
        gameinfo = df_gameinfo.iloc[0]
        stadium_text = " [{0}=KBOT]".format(gameinfo['Stadium'])

        article_dict['article'] = article_text.rstrip('\n\n') + stadium_text
        article_dict['created_at'] = self.change_date_array(args['created_at'])
        lab2ai_conn.insert_article_v2(article_dict)

        return article_dict

    def get_article_text_dict(self, info_list, game_id=None):
        result_dict = {}
        article_list = []
        prev_inning = 0
        top_hitter_dict = {}
        # 오늘 경기 투수 리스트
        df_pitcher_list = self.lab2ai_conn.get_today_game_pitcher_list(game_id)
        pitcher_list = df_pitcher_list['PCODE'].tolist()
        # 타자 정보 추출
        for i, info_dict in enumerate(info_list):
            if info_dict['info']:
                _info = info_dict['info']
                if isinstance(_info, dict):
                    _info_dict = [_info]
                else:
                    _info_dict = _info

                for info in _info_dict:
                    if 'hitter_events' not in info:
                        top_hitter_dict[info['pcode']] = []

        # 문장 합치기
        for i, info_dict in enumerate(info_list):
            if info_dict['p_num'] == 0:
                result_dict['title'] = info_dict['text']
            else:
                if info_dict['info']:
                    _info = info_dict['info']
                    if isinstance(_info, dict):
                        _info_dict = [_info]
                    else:
                        _info_dict = _info

                    for info in _info_dict:
                        if 'hitter_events' not in info:
                            continue
                        for hitter_events in info['hitter_events']:
                            for score_scene in hitter_events['score_scenes']:
                                _hitter_code = score_scene['hitter_or_runner'][0]['pcode']
                                _how = score_scene['how']
                                _how_kor = score_scene['how_kor']
                                hitter_info = self.get_hitter_event(game_id, _hitter_code)
                                data_dict = {'_타격종류': _how_kor, '타자': hitter_info}
                                hitter_sentence_list = self.template.get_sentence_list(data_dict, cfg.TABLE_HALF_INNING_SENTENCE)
                                if hitter_sentence_list:
                                    hitter_event_info = hitter_sentence_list[0]
                                    if _hitter_code in top_hitter_dict:
                                        if hitter_event_info['sentence'] not in top_hitter_dict[_hitter_code]:
                                            top_hitter_dict[_hitter_code].append(hitter_event_info['sentence'])
                                    else:
                                        info_dict['text'] += ' '
                                        info_dict['text'] += hitter_event_info['sentence']

                if isinstance(info_dict['info'], dict) and 'inning' in info_dict['info']:
                    if prev_inning == info_dict['info']['inning']:
                        article_list[-1] += " {}".format(info_dict['text'])
                    else:
                        article_list.append(info_dict['text'])
                        prev_inning = info_dict['info']['inning']
                elif isinstance(info_dict['info'], dict) and 'pcode' in info_dict['info']:  # 주요선수
                    if info_dict['info']['pcode'] in top_hitter_dict:
                        info_dict['text'] += ' '
                        info_dict['text'] += ' '.join(top_hitter_dict[info_dict['info']['pcode']])
                    if info_dict['info']['pcode'] in pitcher_list:
                        pitcher_info = self.get_pitcher_event(game_id, info_dict['info']['pcode'])
                        data_dict = {'투수': pitcher_info}
                        pitcher_sentence_list = self.template.get_sentence_list(data_dict,
                                                                               cfg.TABLE_HALF_INNING_SENTENCE)
                        if pitcher_sentence_list:
                            pitcher_sentence = pitcher_sentence_list[0]
                            info_dict['text'] += ' '
                            info_dict['text'] += pitcher_sentence['sentence']
                    article_list.append(info_dict['text'])
                elif isinstance(info_dict['info'], list) and 'pcode' in info_dict['info'][0]:  # 주요선수
                    for top_info in info_dict['info']:
                        if top_info['pcode'] in top_hitter_dict:
                            info_dict['text'] += ' '
                            info_dict['text'] += ' '.join(top_hitter_dict[top_info['pcode']])
                        if top_info['pcode'] in pitcher_list:
                            pitcher_info = self.get_pitcher_event(game_id, info_dict['info']['pcode'])
                            data_dict = {'투수': pitcher_info}
                            pitcher_sentence_list = self.template.get_sentence_list(data_dict,
                                                                                   cfg.TABLE_HALF_INNING_SENTENCE)
                            if pitcher_sentence_list:
                                pitcher_sentence = pitcher_sentence_list[0]
                                info_dict['text'] += ' '
                                info_dict['text'] += pitcher_sentence['sentence']
                    article_list.append(info_dict['text'])
                else:
                    article_list.append(info_dict['text'])

        result_dict['article'] = article_list
        return result_dict
    # endregion [ARTICLE CONTROL FUNCTION]

    # region [ETC FUNCTIONS]
    def get_variable_dict(self, data):
        variable_list = []
        if isinstance(data, dict):
            for k, v in data.items():
                variable_list.append({'key': k, 'value': self.get_variable_dict(v)})

            _final_val = self.template.set_variable(variable_list)
            return _final_val
        else:
            return data

    def get_gameinfo_dict_list(self):
        df_gameinfo = self.lab2ai_conn.get_gameinfo()
        df_gameinfo = df_gameinfo.sort_values(by='Gday', ascending=False)

        s_gameinfo = df_gameinfo.groupby('Gday')['GmKey'].apply(list).sort_index(ascending=False)
        gameinfo_dict = s_gameinfo.to_dict()
        result = OrderedDict(sorted(gameinfo_dict.items(), reverse=True))

        result_list = []

        for game_day, game_id_list in result.items():
            game_list = []
            for game_id in game_id_list:
                top = game_id[8:10]
                bottom = game_id[10:12]
                game_kor = "{}:{}".format(self.record.MINOR_TEAM_NAME[top],
                                          self.record.MINOR_TEAM_NAME[bottom])
                game_list.append({'game_id': game_id, 'game_kor': game_kor})
            result_list.append({'game_day': game_day, 'game_list': game_list})

        return result_list

    def get_article(self, game_id):
        df_gameinfo = self.lab2ai_conn.get_article_from_db(game_id)
        if df_gameinfo.empty:
            return None
        else:
            return df_gameinfo.to_dict('records')

    def get_article_v2(self, game_id):
        df_gameinfo = self.lab2ai_conn.get_article_from_db_v2(game_id)
        if df_gameinfo.empty:
            return None
        else:
            return df_gameinfo.to_dict('records')

    @classmethod
    def change_date_array(cls, date_time):
        d = date_time
        result = datetime.strptime(d, "%Y-%d-%m %X").strftime("%Y-%m-%d %X")
        return result
    # endregion [ETC FUNCTIONS]


class GspreadTemplate(object):
    template = gsheet_conn.Gspread()
    lab2ai_conn = Lab2AIConnector()

    @classmethod
    def get_template_tab_list(cls):
        return cls.template.get_sheet_tab_list()

    @classmethod
    def set_rds_template_from_gspread(cls, table_name, table_hash):
        rds_table_nm = cfg.GSPREAD_MATCHING_DICT[table_name]
        # delete
        cls.lab2ai_conn.delete_rds_db_by_name(rds_table_nm)
        df_table = pd.DataFrame(table_hash)

        for r_dict in df_table.to_dict('records'):
            # insert
            cls.lab2ai_conn.insert_rds_db_by_name(rds_table_nm, r_dict)
