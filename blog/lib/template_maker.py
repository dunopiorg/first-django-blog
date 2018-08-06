from .. import config as cfg
from ..models import Lab2AIConnector
from .gsheet_conn import Gspread
from korean import l10n

import random


class Template(object):

    def __init__(self):
        self.google_sheet = Gspread()
        self.lab2ai_conn = Lab2AIConnector()
        # self.PITCHER_DB = self.google_sheet.get_df_sheet_by_name(cfg.PITCHER_SENTENCE)
        # self.HITTER_DB = self.google_sheet.get_df_sheet_by_name(cfg.HITTER_SENTENCE)
        # self.TEAM_SENTENCE_DB = self.google_sheet.get_df_sheet_by_name(cfg.TEAM_SENTENCE)
        # self.TEAM_PARAGRAPH_DB = self.google_sheet.get_df_sheet_by_name(cfg.TEAM_PARAGRAPH)
        self.TEAM_SENTENCE_DB = self.lab2ai_conn.get_template_db_by_name(cfg.TABLE_TEAM_SENTENCE)
        self.TEAM_PARAGRAPH_DB = self.lab2ai_conn.get_template_db_by_name(cfg.TABLE_TEAM_PARAGRAPH)

        # region [문장생성]
    def get_team_sentence_list(self, data_list):
        result_list = []
        df_team_db = self.TEAM_SENTENCE_DB.sort_values(by=[cfg.CATEGORY, cfg.PRIORITY])
        category_list = list(df_team_db[cfg.CATEGORY].unique())

        for data_dict in data_list:
            if data_dict[cfg.CATEGORY] in category_list:
                df_tmp = df_team_db[df_team_db[cfg.CATEGORY] == data_dict[cfg.CATEGORY]]
                for i, row in df_tmp.iterrows():
                    row_condition = row[cfg.CONDITIONS]
                    str_condition = row_condition.format(**data_dict)
                    if eval(str_condition):
                        row[cfg.SENTENCE] = self.get_text(row[cfg.SENTENCE], data_dict)
                        result_list.append(row.to_dict())
                        break

        return result_list

    def get_team_paragraph(self, data_df, data_dict):
        result_list = []
        if data_df.empty:
            return result_list
        else:
            df_data = data_df
        team_para_db = self.TEAM_PARAGRAPH_DB.sort_values(by=[cfg.SUBJECT, cfg.CATEGORY, cfg.INDEX])
        subject_list = list(team_para_db[cfg.SUBJECT].unique())
        for sub in subject_list:
            df_sub_data = df_data[df_data[cfg.SUBJECT] == sub]
            if df_sub_data.empty:
                return result_list
            df_sub_db = team_para_db[team_para_db[cfg.SUBJECT] == sub]
            sub_data_keys = list(df_sub_data[cfg.CATEGORY].unique())
            for i, row_sub_db in df_sub_db.iterrows():
                category_dict = self.get_string_to_dict(row_sub_db[cfg.CATEGORY_DICT])
                category_dict_keys = list(category_dict.keys())
                is_subset_catg = set(category_dict_keys).issubset(sub_data_keys)
                if not is_subset_catg:
                    continue
                is_same_index, _dict = self.is_prime(category_dict, df_sub_data)
                data_dict.update(_dict)
                if is_same_index:
                    paragraph_text = self.get_text(row_sub_db[cfg.SENTENCE], data_dict)
                    result_list.append(paragraph_text)
                    break

        return result_list
    # endregion [문장생성]

    # region [FUNCTIONS]
    def get_text(self, template, data_dict):
        text = ''
        temp_list = [d.strip() for d in template.split('#') if d]  # 공백제거
        s = random.choice(temp_list)
        if s:
            text = l10n.Template(s).format(**data_dict)
        return text

    def get_string_to_dict(self, str_dict):
        result_dict = {}
        str_list = [d for d in str_dict.split(',') if d]
        for s in str_list:
            s_tmp = s.split(':')
            result_dict[s_tmp[0]] = s_tmp[1]
        return result_dict

    def is_prime(self, data_dict, df_rows):
        result_flag = False
        result_dict = {}
        data_keys = list(data_dict.keys())
        for k in data_keys:
            df_a_row = df_rows[df_rows[cfg.CATEGORY] == k]
            _index = df_a_row[cfg.INDEX].values[0]
            if _index > 0:
                data_index = 1
            elif _index < 0:
                data_index = -1
            else:
                data_index = _index

            result_dict[k] = df_a_row[cfg.SENTENCE].values[0]

            if int(data_dict[k]) == data_index:
                result_flag = True
            else:
                result_flag = False

        return result_flag, result_dict
    # endregion [FUNCTIONS]
