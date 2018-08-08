from .models import Lab2AIConnector
from .lib.template_maker import Template
from .lib.records import Records
from .lib import gsheet_conn
from . import config as cfg
import pandas as pd


class RecordApp(object):
    def __init__(self):
        self.lab2ai_conn = Lab2AIConnector()
        self.record = Records()
        self.template = Template()

    class TeamStructure(object):
        pass

    # region [TEAM EVENT]
    def get_team_paragraph(self, win_team, loss_team, game_id):
        sentence_list = []
        data_dict = {'승리팀': self.record.MINOR_TEAM_NAME[win_team], '패배팀': self.record.MINOR_TEAM_NAME[loss_team]}
        win_team_data = self.record.get_team_win_record(win_team, game_id)
        if win_team_data:
            sentence_list.extend(win_team_data)

        loss_team_data = self.record.get_team_loss_record(loss_team, game_id)
        if loss_team_data:
            sentence_list.extend(loss_team_data)

        versus_team_data = self.record.get_team_versus_record(win_team, loss_team, game_id)
        if versus_team_data:
            sentence_list.extend(versus_team_data)

        print(sentence_list)
        result_sentence = self.template.get_team_sentence_list(sentence_list)
        df_result_sentence = pd.DataFrame(result_sentence)
        if df_result_sentence.empty:
            return ''
        result_paragraph = self.template.get_team_paragraph(df_result_sentence, data_dict)

        return result_paragraph

    def get_team_info(self, game_id):
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
        result = ' '.join(result_list)

        return result
    # endregion [TEAM EVENT]

    # region [HITTER EVENT]
    def get_player_event_dict(self, game_id, player_name=None, hitter_code=None, pitcher_code=None):
        result_list = []
        if hitter_code:
            # hitter
            result_list.append(self.record.get_hitter_n_continue_record(hitter_code))
            result_list.append(self.record.get_hitter_prev_record(hitter_code))
            result_list.append(self.record.get_hitter_first_hr(hitter_code, game_id))
        else:
            # pitcher
            result_list.append(self.record.get_pitcher_unit_record(pitcher_code))
            result_list.append(self.record.get_pitcher_how_long_days(pitcher_code))
            result_list.append(self.record.get_pitcher_gamecontapp(pitcher_code, game_id))
            # result_list.append(self.record.get_pitcher_how_many_games(pitcher_code))
            result_list.append(self.record.get_pitcher_season_record(pitcher_code))
        return {'game_id': game_id, 'player_records': result_list, 'player_name': player_name}
    # endregion [HITTER EVENT]


class GspreadTemplate(object):
    template = gsheet_conn.Gspread()
    lab2ai_conn = Lab2AIConnector()

    @classmethod
    def get_template_tab_list(cls):
        return cls.template.get_sheet_tab_list()

    @classmethod
    def set_rds_template_from_gspread(cls, table_name, table_hash):
        rds_table_nm = cfg.SHEET_MATCHING_DICT[table_name]
        # delete
        cls.lab2ai_conn.delete_rds_db_by_name(rds_table_nm)
        df_table = pd.DataFrame(table_hash)

        for r_dict in df_table.to_dict('records'):
            # insert
            cls.lab2ai_conn.insert_rds_db_by_name(rds_table_nm, r_dict)
