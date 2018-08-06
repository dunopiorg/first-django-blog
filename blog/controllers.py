from .models import Lab2AIConnector
from .lib.template_maker import Template
from .lib.records import Records
import pandas as pd


class RecordApp(object):

    def __init__(self):
        self.lab2ai_conn = Lab2AIConnector()
        self.record = Records()
        self.template = Template()

    # region [TEAM EVENT]
    def get_team_paragraph(self, win_team, loss_team, game_id):
        result = []
        data_dict = {'승리팀': self.record.MINOR_TEAM_NAME[win_team], '패배팀': self.record.MINOR_TEAM_NAME[loss_team]}
        win_team_data = self.record.get_team_win_record(win_team)
        loss_team_data = self.record.get_team_loss_record(loss_team)
        versus_team_data = self.record.get_team_versus_record(win_team, loss_team)

        data_list = [win_team_data[0], loss_team_data[0], versus_team_data[0]]
        result_sentence = self.template.get_team_sentence_list(data_list)
        df_result_sentence = pd.DataFrame(result_sentence)
        result_paragraph = self.template.get_team_paragraph(df_result_sentence, data_dict)
        result.append({game_id: ' '.join(result_paragraph)})
        return result

    def test_get_team(self):
        result_list = []
        df_all_score = self.lab2ai_conn.get_test_team_scores('20180630KTHH0')
        for i, row in df_all_score.iterrows():
            game_id = row['GMKEY']
            t_socre = row['TPOINT']
            b_socre = row['BPOINT']

            if t_socre > b_socre:
                win_team = game_id[8:10]
                loss_team = game_id[10:12]
                result_list.append(self.get_team_paragraph(win_team, loss_team, game_id))
            elif t_socre < b_socre:
                loss_team = game_id[8:10]
                win_team = game_id[10:12]
                result_list.append(self.get_team_paragraph(win_team, loss_team, game_id))

        return result_list

    # endregion [TEAM EVENT]

    # region [HITTER EVENT]
    def get_player_event_dict(self, game_id, hitter_code=None, pitcher_code=None):
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
            result_list.append(self.record.get_pitcher_gamecontapp(pitcher_code))
            result_list.append(self.record.get_pitcher_how_many_games(pitcher_code))
            result_list.append(self.record.get_pitcher_season_record(pitcher_code))
        return {'game_id': game_id, 'player_records': result_list}

    # endregion [HITTER EVENT]
    def set_rds_database_from_gsheet(self):
        df_team_sentence_db = self.template.TEAM_SENTENCE_DB

        print(self.lab2ai_conn.delete_rds_db_team_sentence())
        for i, row in df_team_sentence_db.iterrows():
            print(self.lab2ai_conn.set_rds_db_team_sentence(row))

