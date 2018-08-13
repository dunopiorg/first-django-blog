import pandas as pd
import gspread
from .. import config
from oauth2client.service_account import ServiceAccountCredentials


class Gspread(object):

    def get_df_sheet_by_index(self, index_num):
        scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(config.GSHEET_CONFIG_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open(config.GSHEET_DB_NAME)
        worksheet = sheet.get_worksheet(index_num)

        list_of_hashes = worksheet.get_all_records()
        if list_of_hashes:
            df_template = pd.DataFrame(list_of_hashes)
            return df_template
        else:
            return None

    def get_df_sheet_by_name(self, sheet_name):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(config.GSHEET_CONFIG_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open(config.GSHEET_DB_NAME)
        worksheet = sheet.worksheet(sheet_name)

        list_of_hashes = worksheet.get_all_records()
        if list_of_hashes:
            df_template = pd.DataFrame(list_of_hashes)
            return df_template
        else:
            return None

    def get_sheet_tab_list(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(config.GSHEET_CONFIG_DICT, scope)
        client = gspread.authorize(creds)
        sheet = client.open(config.GSHEET_DB_NAME)
        return sheet.worksheets()
