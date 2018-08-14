from ..models import Lab2AIConnector
from datetime import datetime
from .. import config as cfg


class Records(object):
    lab2ai_conn = Lab2AIConnector()

    def __init__(self):
        self.lab2ai_conn = Lab2AIConnector()
        self.MINOR_TEAM_NAME = self.get_minor_team_name()
        self.KBO_TEAM_NAME = self.get_kbo_team_name()
        self._PA = cfg.PA
        self._AB = cfg.AB
        self._HIT = cfg.HIT

    # region [ETC FUNCTIONS]
    @classmethod
    def get_date_kor(cls, game_date, record_date):
        game_dt = datetime.strptime(game_date, '%Y%m%d')
        record_dt = datetime.strptime(record_date, '%Y%m%d')
        dt = game_dt - record_dt
        if dt.days > 25:
            s_format = "{0}월 {1}일".format(record_dt.month, record_dt.day)
        else:
            s_format = "지난 {0}일".format(record_dt.day)

        return s_format

    @classmethod
    def get_minor_team_name(cls):
        df_team = cls.lab2ai_conn.get_minor_team_name_info()
        return df_team.set_index('team')['teamname'].to_dict()

    @classmethod
    def get_kbo_team_name(cls):
        df_team = cls.lab2ai_conn.get_kbo_team_name_info()
        return df_team.set_index('team')['team_kor'].to_dict()

    def set_wls_score(self, df_score, team_code):
        df = df_score
        wls_list = []
        for i, row in df.iterrows():
            game_key = row['GMKEY']
            if row['9T'] == -1:
                wls_list.append('D')
            elif game_key[8:10] == team_code:
                if row['TPOINT'] > row['BPOINT']:
                    wls_list.append('W')
                elif row['TPOINT'] < row['BPOINT']:
                    wls_list.append('L')
                else:
                    wls_list.append('D')
            else:
                if row['TPOINT'] < row['BPOINT']:
                    wls_list.append('W')
                elif row['TPOINT'] > row['BPOINT']:
                    wls_list.append('L')
                else:
                    wls_list.append('D')
        df['WLS'] = wls_list
        return df
    # endregion [ETC FUNCTIONS]

    # region [HITTER EVENT]
    def get_hitter_n_continue_record(self, game_id, hitter_code):
        how_dict = {'안타': self._HIT, '홈런': ['HR'], '2루타': ['H2'], '3루타': ['H3'],
                    '출루': ['H1', 'H2', 'H3', 'HR', 'HI', 'HB', 'BB']}
        place_dict = {'타점': ['E', 'R', 'H']}
        # n_pa_count_dict = {'HIT': 3, 'HR': 2, 'H2': 2, 'H3': 2, 'RBI': 3, 'OB': 5}
        # n_game_count_dict = {'HIT': 5, 'HR': 2, 'H2': 2, 'H3': 2, 'RBI': 5, 'OB': 10}
        result_list = []

        data_dict = {}
        game_date = game_id[0:8]
        df = self.lab2ai_conn.get_hitter_gamecontapp_record(hitter_code, game_date=game_date, limit=200)

        s_temp = df.iloc[0]
        if s_temp['TB'] == 'T':
            hitter_team_cd = s_temp['GMKEY'][8:10]
        else:
            hitter_team_cd = s_temp['GMKEY'][10:12]

        if df.empty:
            return None
        else:
            df_game = df[['GMKEY', 'HOW', 'PLACE']]
            s_how = df_game.groupby('GMKEY')['HOW'].apply(list)
            s_place = df_game.groupby('GMKEY')['PLACE'].apply(list)

        s_how = s_how.sort_index(ascending=False)
        s_place = s_place.sort_index(ascending=False)

        # N경기 안타, 출루 셋팅
        n_game_continue = {}
        for how_k, how_v in how_dict.items():
            n_game_counter = 0
            for i, (s_index, hows) in enumerate(s_how.items()):
                if i == n_game_counter and any(item in how_v for item in hows):
                    n_game_counter += 1
                else:
                    if s_index[8:10] == hitter_team_cd:
                        vs_team_cd = s_index[10:12]
                    else:
                        vs_team_cd = s_index[8:10]

                    n_game_continue[how_k] = {
                        '날짜': self.get_date_kor(game_date, s_index[0:8]),
                        '경기수': n_game_counter,
                        '상대팀': self.MINOR_TEAM_NAME[vs_team_cd]
                    }
                    break

        # N경기 타점 셋팅
        for place_k, place_v in place_dict.items():
            n_game_counter = 0
            for i, (s_index, places) in enumerate(s_place.items()):
                if i == n_game_counter and any(item in place_v for item in places):
                    n_game_counter += 1
                else:
                    if s_index[8:10] == hitter_team_cd:
                        vs_team_cd = s_index[10:12]
                    else:
                        vs_team_cd = s_index[8:10]

                    n_game_continue[place_k] = {
                        '날짜': self.get_date_kor(game_date, s_index[0:8]),
                        '경기수': n_game_counter,
                        '상대팀': self.MINOR_TEAM_NAME[vs_team_cd]
                    }
                    break

        s_pa_how = df_game['HOW']
        s_pa_place = df_game['PLACE']

        # N타석 안타, 출루 셋팅
        n_pa_counter = {}
        for how_k, how_v in how_dict.items():
            n_pa_counter[how_k] = 0
            for i, how in enumerate(s_pa_how.values):
                if i == n_pa_counter[how_k] and how in how_v:
                    n_pa_counter[how_k] += 1
                else:
                    break

        # N타석 타점 셋팅
        for place_k, place_v in place_dict.items():
            n_pa_counter[place_k] = 0
            for i, place in enumerate(s_pa_place.values):
                if i == n_pa_counter[place_k] and place in place_v:
                    n_pa_counter[place_k] += 1
                else:
                    break

        # N경기 만에 안타, 출루 셋팅
        n_game_last = {}
        for how_k, how_v in how_dict.items():
            n_game_last_counter = 0
            for i, (s_index, hows) in enumerate(s_how.items()):
                if i == n_game_last_counter and not any(item in how_v for item in hows):
                    n_game_last_counter += 1
                else:
                    if s_index[8:10] == hitter_team_cd:
                        vs_team_cd = s_index[10:12]
                    else:
                        vs_team_cd = s_index[8:10]

                    n_game_last_counter += 1
                    n_game_last[how_k] = {
                        '날짜': self.get_date_kor(game_date, s_index[0:8]),
                        '경기수': n_game_last_counter,
                        '상대팀': self.MINOR_TEAM_NAME[vs_team_cd]
                    }
                    break

        # N경기 안타, 출루 기록
        # for how_k, counter in n_game_counter.items():
        #     if counter > n_game_count_dict[how_k]:
        #         n_game_dict = data_dict.copy()
        #         n_game_dict['RESULT'] = counter
        #         n_game_dict['STATE'] = how_k
        #         n_game_dict[cfg.CATEGORY] = "N게임_연속_안타_출루"
        #         result_list.append(n_game_dict)

        #n경기 기록
        # data_dict['n타석_연속'] = n_game_counter
        #
        # # N경기 연속 안타
        # n_game_hit_dict = data_dict.copy()
        # n_game_hit_dict['경기수'] = n_game_count_dict['HIT']
        # n_game_hit_dict[cfg.CATEGORY] = "N게임_연속_안타"
        # result_list.append(n_game_hit_dict)
        #
        # # N경기 연속 홈런
        # n_game_hr_dict = data_dict.copy()
        # n_game_hr_dict['경기수'] = n_game_count_dict['HR']
        # n_game_hr_dict[cfg.CATEGORY] = "N게임_연속_홈런"
        # result_list.append(n_game_hr_dict)
        #
        # # N경기 연속 2루타
        # n_game_h2_dict = data_dict.copy()
        # n_game_h2_dict['경기수'] = n_game_count_dict['H2']
        # n_game_h2_dict[cfg.CATEGORY] = "N게임_연속_2루타"
        # result_list.append(n_game_h2_dict)
        #
        # # N경기 연속 2루타
        # n_game_h3_dict = data_dict.copy()
        # n_game_h3_dict['경기수'] = n_game_count_dict['H3']
        # n_game_h3_dict[cfg.CATEGORY] = "N게임_연속_3루타"
        # result_list.append(n_game_h3_dict)
        #
        # # N경기 연속 출루
        # n_game_ob_dict = data_dict.copy()
        # n_game_ob_dict['경기수'] = n_game_count_dict['OB']
        # n_game_ob_dict[cfg.CATEGORY] = "N게임_연속_출루"
        # result_list.append(n_game_ob_dict)
        #
        # # N경기 연속 타점
        # n_game_rbi_dict = data_dict.copy()
        # n_game_rbi_dict['경기수'] = n_game_count_dict['RBI']
        # n_game_rbi_dict[cfg.CATEGORY] = "N게임_연속_타점"
        # result_list.append(n_game_rbi_dict)

        # N경기 타점 기록
        # for place_k, counter in n_game_rbi_counter.items():
        #     if counter > n_game_count_dict[place_k]:
        #         n_game_rbi_dict = data_dict.copy()
        #         n_game_rbi_dict['RESULT'] = counter
        #         n_game_rbi_dict['STATE'] = place_k
        #         n_game_rbi_dict[cfg.CATEGORY] = "N게임_연속_타점"
        #         result_list.append(n_game_rbi_dict)

        # N타석 안타, 출루 기록
        # for pa_how_k, counter in n_pa_counter.items():
        #     if counter > n_pa_count_dict[pa_how_k]:
        #         n_pa_dict = data_dict.copy()
        #         n_pa_dict['RESULT'] = counter
        #         n_pa_dict['STATE'] = pa_how_k
        #         n_pa_dict[cfg.CATEGORY] = "N타석_연속_안타_출루"
        #         result_list.append(n_pa_dict)

        # # N타석 연속 안타
        # n_pa_hit_dict = data_dict.copy()
        # n_pa_hit_dict['타석수'] = n_pa_count_dict['HIT']
        # n_pa_hit_dict[cfg.CATEGORY] = "N타석_연속_안타"
        # result_list.append(n_pa_hit_dict)
        #
        # # N타석 연속 홈런
        # n_pa_hit_dict = data_dict.copy()
        # n_pa_hit_dict['타석수'] = n_pa_count_dict['HR']
        # n_pa_hit_dict[cfg.CATEGORY] = "N타석_연속_홈런"
        # result_list.append(n_pa_hit_dict)
        #
        # # N타석 연속 2루타
        # n_pa_h2_dict = data_dict.copy()
        # n_pa_h2_dict['타석수'] = n_pa_count_dict['H2']
        # n_pa_h2_dict[cfg.CATEGORY] = "N타석_연속_2루타"
        # result_list.append(n_pa_h2_dict)
        #
        # # N타석 연속 3루타
        # n_pa_h3_dict = data_dict.copy()
        # n_pa_h3_dict['타석수'] = n_pa_count_dict['H3']
        # n_pa_h3_dict[cfg.CATEGORY] = "N타석_연속_3루타"
        # result_list.append(n_pa_h3_dict)
        #
        # # N타석 연속 출루
        # n_pa_ob_dict = data_dict.copy()
        # n_pa_ob_dict['타석수'] = n_pa_count_dict['OB']
        # n_pa_ob_dict[cfg.CATEGORY] = "N타석_연속_출루"
        # result_list.append(n_pa_ob_dict)
        #
        # # N타석 연속 타점
        # n_pa_rbi_dict = data_dict.copy()
        # n_pa_rbi_dict['타석수'] = n_pa_count_dict['RBI']
        # n_pa_rbi_dict[cfg.CATEGORY] = "N타석_연속_타점"
        # result_list.append(n_pa_rbi_dict)

        # N타석 타점 기록
        # for pa_rbi_k, counter in n_pa_rbi_counter.items():
        #     if counter > n_pa_count_dict[pa_rbi_k]:
        #         n_pa_rbi_dict = data_dict.copy()
        #         n_pa_rbi_dict['RESULT'] = counter
        #         n_pa_rbi_dict['STATE'] = pa_rbi_k
        #         n_pa_rbi_dict[cfg.CATEGORY] = "N타석_연속_타점"
        #         result_list.append(n_pa_rbi_dict)

        return n_game_continue, n_game_last

    def get_hitter_named(self, hitter_code, team_code=None):
        df_score = self.lab2ai_conn.get_score(2018, 'SK')

        df_hitter = self.lab2ai_conn.get_kbo_hitter_total(hitter_code)
        if df_hitter.empty:
            return None

    def get_hitter_prev_record(self, hitter_code):
        """
        홈런 또는 멀티히트
        :param hitter_code:
        :return:
        """
        data_dict = {'HITTER': hitter_code}
        result_list = []

        df_hitter = self.lab2ai_conn.get_hitter(hitter_code, 5)
        now = datetime.now()
        df_prev = df_hitter.query("GDAY<'{}{}{}'".format(now.year, now.month, now.day))
        df_prev = df_prev.sort_values(by=['GDAY'], ascending=False)

        s_prev = df_prev.iloc[0]

        if s_prev['HIT'] == 0:
            return None

        game_id = s_prev['GMKEY']
        tb = s_prev['TB']
        game_date = datetime(int(game_id[0:4]), int(game_id[4:6]), int(game_id[6:8]))
        game_day = "{0}월 {1}일".format(game_date.month, game_date.day)
        if tb == 'T':
            versus_team = self.MINOR_TEAM_NAME[game_id[10:12]]
        else:
            versus_team = self.MINOR_TEAM_NAME[game_id[8:10]]

        if s_prev['HIT'] >= 2 and s_prev['HR'] > 0:
            multi_hit_hr_dict = data_dict.copy()
            multi_hit_hr_dict['안타수'] = s_prev['HIT']
            multi_hit_hr_dict['홈런수'] = s_prev['HR']
            multi_hit_hr_dict['일자'] = game_day
            multi_hit_hr_dict['상대팀'] = versus_team
            multi_hit_hr_dict[cfg.CATEGORY] = "이전경기_홈런포함_멀티히트"
            result_list.append(multi_hit_hr_dict)
        elif s_prev['HIT'] >= 2:
            multi_hit_dict = data_dict.copy()
            multi_hit_dict['안타수'] = s_prev['HIT']
            multi_hit_dict['일자'] = game_day
            multi_hit_dict['상대팀'] = versus_team
            multi_hit_dict[cfg.CATEGORY] = "이전경기_멀티히트"
            result_list.append(multi_hit_dict)
        elif s_prev['HR'] > 0:
            multi_hr_dict = data_dict.copy()
            multi_hr_dict['홈런수'] = s_prev['HR']
            multi_hr_dict['일자'] = game_day
            multi_hr_dict['상대팀'] = versus_team
            multi_hr_dict[cfg.CATEGORY] = "이전경기_홈런"
            result_list.append(multi_hr_dict)
        else:
            return None

        return result_list

    def get_hitter_first_hr(self, hitter_code, game_key):
        """
        시즌 첫 홈런일 경우 또는 첫 경기 홈런일 경우
        :param hitter_code:
        :param game_key:
        :return:
        """
        data_dict = {'선수코드': hitter_code, '경기': 'SEASON'}
        result_list = []

        df_hitter = self.lab2ai_conn.get_hitter(hitter_code)
        s_hitter = df_hitter.iloc[0]

        if df_hitter.shape[0] == 1:
            first_hr_dict = data_dict.copy()
            first_hr_dict['홈런수'] = s_hitter['HR']
            first_hr_dict[cfg.CATEGORY] = "개인_시즌_첫_경기_홈런"
            result_list.append(first_hr_dict)
            return result_list

        now = datetime.now()
        df_prev = df_hitter.query("GDAY<'{}{}{}'".format(now.year, now.month, now.day))
        df_prev = df_prev.sort_values(by=['GDAY'], ascending=False)

        today_hr = s_hitter['HR']
        prev_hr = df_prev['HR'].sum()
        pa = df_hitter['PA'].sum()

        if today_hr > 0 and prev_hr == 0:
            game_date = game_key[0:8]
            df_hitter_gamecont = self.lab2ai_conn.get_hitter_gamecontapp_record(hitter_code, game_date=game_date, game_key=game_key)

            for i, row in df_hitter_gamecont.iterrows():
                if row['HOW'] in self._PA:
                    pa += 1
                if row['HOW'] == 'HR':
                    break

            first_hr_dict = data_dict.copy()
            first_hr_dict['경기수'] = df_hitter.shape[0]
            first_hr_dict['타석수'] = pa
            first_hr_dict[cfg.CATEGORY] = "개인_시즌_첫_홈런"
            result_list.append(first_hr_dict)
            return result_list

    def get_kbo_hitter_record(self, hitter_code):
        df_injury = self.lab2ai_conn.get_injury(hitter_code)

        if df_injury.empty:
            return None
        else:
            s_injury = df_injury.iloc[0]
        # state_nm : 1군복귀, 퓨처스복귀, 엔트리유지, 재활중, 치료중(수술포함)

    @classmethod
    def get_hitter_final_hit(cls, game_id):
        data_dict = dict()
        data_dict['존재여부'] = False
        lab2ai_conn = Lab2AIConnector()
        df_record_matrix = lab2ai_conn.get_ie_record_matrix_mix(game_id)
        df_record_matrix = df_record_matrix.sort_values(by='SEQNO', ascending=False)

        index_cnt = 0
        for i, row in df_record_matrix.iterrows():
            if index_cnt == 0 and row['AFTER_SCORE_GAP_CN'] == 0:
                return data_dict
            else:
                index_cnt += 1
                if row['AFTER_SCORE_GAP_CN'] == 0:
                    s_record = df_record_matrix.iloc[index_cnt - 2]
                    team_name = cls.get_minor_team_name()

                    hitter_code = s_record['BAT_P_ID']
                    df_person = lab2ai_conn.get_person_info(hitter_code)
                    s_person = df_person.iloc[0]
                    if s_record['AFTER_SCORE_GAP_CN'] > 0:
                        win_team = team_name[game_id[10:12]]
                    else:
                        win_team = team_name[game_id[8:10]]

                    how_code = s_record['HOW_ID']
                    if how_code not in cfg.HIT:
                        return data_dict
                    else:
                        how_code = cfg.HOW_KOR_DICT[how_code]

                    inn_no = s_record['INN_NO']
                    data_dict['선수명'] = s_person['NAME']
                    data_dict['선수코드'] = str(hitter_code)
                    data_dict['팀명'] = win_team
                    data_dict['타격종류'] = how_code
                    data_dict['이닝'] = inn_no
                    data_dict['존재여부'] = True
                    return data_dict
    # endregion [HITTER EVENT]

    # region [PITCHER EVENT]
    def get_pitcher_unit_record(self, pitcher_code):
        """
        시즌 첫 승, 10단위 승
        :param pitcher_code:
        :return:
        """
        data_dict = {'선수코드': pitcher_code, '경기': 'SEASON'}
        result_list = []
        df_pitcher_total = self.lab2ai_conn.get_pitcher_total(pitcher_code, datetime.now().year)
        s_pitcher = df_pitcher_total.iloc[0]

        if s_pitcher['W'] == 1 and s_pitcher['GAMENUM'] == 1 and df_pitcher_total.shape[0] > 1:
            first_w_dict = data_dict.copy()
            first_w_dict[cfg.CATEGORY] = "시즌_첫승"
            result_list.append(first_w_dict)
        elif s_pitcher['W'] % 10 == 0:
            first_w_dict = data_dict.copy()
            first_w_dict['승수'] = s_pitcher['W']
            first_w_dict[cfg.CATEGORY] = "10단위_승"
            result_list.append(first_w_dict)
        else:
            return None

        return result_list

    def get_pitcher_named(self, pitcher_code, team_code=None):
        df_score = self.lab2ai_conn.get_score(2018, 'SK')

        df_pitcher = self.lab2ai_conn.get_kbo_pitcher_total(pitcher_code)
        if df_pitcher.empty:
            return None

    def get_pitcher_how_long_days(self, pitcher_code):
        """
        며칠만에 등판 승리
        :param pitcher_code:
        :return:
        """
        data_dict = {'선수코드': pitcher_code, '경기': 'SEASON'}
        result_list = []
        last_minor = True

        df_minor_pitcher = self.lab2ai_conn.get_pitcher(pitcher_code, 2)
        df_kbo_pitcher = self.lab2ai_conn.get_kbo_pitcher(pitcher_code, 1)

        s_today_pitcher = df_minor_pitcher.iloc[0]

        if df_kbo_pitcher.empty:
            s_kbo_pitcher = None
        else:
            s_kbo_pitcher = df_kbo_pitcher.iloc[0]

        if df_minor_pitcher.shape[0] == 1:
            total_first_win_dict = data_dict.copy()
            total_first_win_dict[cfg.CATEGORY] = "첫등판_첫승"
            result_list.append(total_first_win_dict)
            return result_list
        else:
            s_last_pitcher_minor = df_minor_pitcher.iloc[1]

        if s_kbo_pitcher is not None:
            if s_kbo_pitcher['GDAY'] > s_last_pitcher_minor['GDAY']:
                last_minor = False

        date_format = "%Y%m%d"
        d0 = datetime.strptime(s_today_pitcher['GDAY'], date_format)

        if last_minor:
            d1 = datetime.strptime(s_last_pitcher_minor['GDAY'], date_format)
            game_id = s_last_pitcher_minor['GMKEY']
            tb = s_last_pitcher_minor['TB']
        else:
            d1 = datetime.strptime(s_kbo_pitcher['GDAY'], date_format)
            game_id = s_kbo_pitcher['GMKEY']
            tb = s_kbo_pitcher['TB']

        date_delta = d0 - d1
        game_date = datetime(int(game_id[0:4]), int(game_id[4:6]), int(game_id[6:8]))
        game_day = "{0}월 {1}일".format(game_date.month, game_date.day)

        if tb == 'T':
            if last_minor:
                versus_team = self.MINOR_TEAM_NAME[game_id[10:12]]
            else:
                versus_team = self.KBO_TEAM_NAME[game_id[10:12]]
        else:
            if last_minor:
                versus_team = self.MINOR_TEAM_NAME[game_id[8:10]]
            else:
                versus_team = self.KBO_TEAM_NAME[game_id[8:10]]
        if last_minor:
            league_name = '퓨처스리그'
        else:
            league_name = 'KBO리그'

        long_days_dict = data_dict.copy()
        long_days_dict['며칠'] = date_delta.days
        long_days_dict['일자'] = game_day
        long_days_dict['리그'] = league_name
        long_days_dict['상대팀'] = versus_team
        long_days_dict[cfg.CATEGORY] = "며칠_등판_승"
        result_list.append(long_days_dict)

        return result_list

    def get_pitcher_gamecontapp(self, pitcher_code, game_id):
        """
        오늘 득점권 상황에서 피안타율
        :param pitcher_code:
        :param game_id:
        :return:
        """
        data_dict = {'선수코드': pitcher_code, '경기': 'TODAY'}
        result_list = []
        df_game = self.lab2ai_conn.get_pitcher_gamecontapp_record(pitcher_code, game_id)
        df_game = df_game.query("BASE2B != '' or BASE3B != ''")
        how_list = df_game['HOW'].tolist()

        ab_count = 0
        hit_count = 0

        for how in how_list:
            if how in self._AB:
                ab_count += 1
            if how in self._HIT:
                hit_count += 1

        if ab_count == 0:
            return result_list
        avg = round(hit_count / ab_count, 3)

        long_days_dict = data_dict.copy()
        long_days_dict['피안타율'] = str(avg)
        long_days_dict[cfg.CATEGORY] = "오늘_득점권_피안타율"
        result_list.append(long_days_dict)

        return result_list

    def get_pitcher_how_many_games(self, pitcher_code):
        data_dict = {'선수코드': pitcher_code, '경기': 'SEASON'}
        result_list = []

        df_minor_pitcher = self.lab2ai_conn.get_pitcher(pitcher_code)

        total_games = df_minor_pitcher.shape[0]

        if total_games == 1:
            return None

        if df_minor_pitcher['WLS'].value_counts()['W'] == 1:
            first_win_dict = data_dict.copy()
            first_win_dict['경기수'] = total_games
            first_win_dict[cfg.CATEGORY] = "데뷔_첫승"
            result_list.append(first_win_dict)
            return result_list
        else:
            games = 1
            game_id = ''
            tb = ''
            for i, row in df_minor_pitcher.iterrows():
                if i == 0:
                    continue
                else:
                    if row['W'] == 'W':
                        game_id = row['GMKEY']
                        tb = row['TB']
                        break
                    else:
                        games += 1

            game_date = datetime(int(game_id[0:4]), int(game_id[4:6]), int(game_id[6:8]))
            game_day = "{0}월 {1}일".format(game_date.month, game_date.day)
            if tb == 'T':
                versus_team = self.MINOR_TEAM_NAME[game_id[10:12]]
            else:
                versus_team = self.MINOR_TEAM_NAME[game_id[8:10]]
            games_win_dict = data_dict.copy()
            games_win_dict['경기수'] = games
            games_win_dict['일자'] = game_day
            games_win_dict['상대팀'] = versus_team
            games_win_dict[cfg.CATEGORY] = "N경기만에_승"
            result_list.append(games_win_dict)
            return result_list

    def get_pitcher_season_record(self, pitcher_code):
        data_dict = {'선수코드': pitcher_code, '경기': 'SEASON'}
        result_list = []

        df_pitcher_total = self.lab2ai_conn.get_pitcher_total(pitcher_code, datetime.now().year)
        s_pitcher_total = df_pitcher_total.iloc[0]
        w = s_pitcher_total['W']
        save = s_pitcher_total['SV']
        hold = s_pitcher_total['HOLD']
        game_num = s_pitcher_total['GAMENUM']
        era = s_pitcher_total['ERA']
        inn = s_pitcher_total['INN']
        r = s_pitcher_total['R']
        er = s_pitcher_total['ER']

        pitcher_season_dict = data_dict.copy()
        pitcher_season_dict['승수'] = w
        pitcher_season_dict['세이브수'] = save
        pitcher_season_dict['홀드수'] = hold
        pitcher_season_dict['경기수'] = game_num
        pitcher_season_dict['평자'] = era
        pitcher_season_dict['이닝'] = inn
        pitcher_season_dict['실점'] = r
        pitcher_season_dict['자책'] = er
        pitcher_season_dict[cfg.CATEGORY] = "투수_주요_기록"
        result_list.append(pitcher_season_dict)
        return result_list

    # endregion [PITCHER EVENT]

    # region [TEAM EVENT]
    def get_team_win_record(self, team_code, game_id):
        data_dict = {cfg.SUBJECT: '팀기록1', cfg.CATEGORY: '승리팀_연승패'}
        result_list = []

        df_score = self.lab2ai_conn.get_team_score(team_code, game_id)
        df_team_score = self.set_wls_score(df_score, team_code)
        wls_list = df_team_score['WLS'].tolist()
        continue_w = 0
        after_w_game_cnt = 1
        after_d_cnt = 0
        continue_l = 0

        for wls in wls_list:
            if wls == 'W':
                continue_w += 1
            else:
                break

        for i, wls in enumerate(wls_list):
            if i == 0:
                continue
            if wls != 'W':
                after_w_game_cnt += 1
                if wls == 'D':
                    after_d_cnt += 1
            else:
                break

        for wls in wls_list:
            if wls == 'L':
                continue_l += 1
            else:
                break

        data_dict['이름'] = self.MINOR_TEAM_NAME[team_code]
        data_dict['승수'] = wls_list.count('W')
        data_dict['패수'] = wls_list.count('L')
        data_dict['무승부'] = wls_list.count('D')
        data_dict['연승수'] = continue_w
        data_dict['직전_연패수'] = continue_l
        data_dict['승_이후_경기수'] = after_w_game_cnt
        data_dict['승_이후_무승부수'] = after_d_cnt
        data_dict['승리팀'] = self.MINOR_TEAM_NAME[team_code]
        # result_list.append(data_dict)

        return data_dict

    def get_team_loss_record(self, team_code, game_id):
        data_dict = {cfg.SUBJECT: '팀기록1', cfg.CATEGORY: '패배팀_연승패'}
        result_list = []

        df_score = self.lab2ai_conn.get_team_score(team_code, game_id)
        df_team_score = self.set_wls_score(df_score, team_code)
        wls_list = df_team_score['WLS'].tolist()

        continue_l = 0
        continue_w = 0
        after_l_game_cnt = 1
        after_d_cnt = 0

        for wls in wls_list:
            if wls == 'L':
                continue_l += 1
            else:
                break

        for wls in wls_list:
            if wls == 'W':
                continue_w += 1
            else:
                break

        for i, wls in enumerate(wls_list):
            if i == 0:
                continue
            if wls != 'L':
                after_l_game_cnt += 1
                if wls == 'D':
                    after_d_cnt += 1
            else:
                break

        data_dict['이름'] = self.MINOR_TEAM_NAME[team_code]
        data_dict['승수'] = wls_list.count('W')
        data_dict['패수'] = wls_list.count('L')
        data_dict['무승부수'] = wls_list.count('D')
        data_dict['연패수'] = continue_l
        data_dict['직전_연승수'] = continue_w
        data_dict['패_이후_경기수'] = after_l_game_cnt
        data_dict['패_이후_무승부수'] = after_d_cnt
        data_dict['패배팀'] = self.MINOR_TEAM_NAME[team_code]
        # result_list.append(data_dict)

        return data_dict

    def get_team_versus_record(self, team_code, versus_team, game_id):
        data_dict = {cfg.SUBJECT: '팀기록2',
                     '승리팀': self.MINOR_TEAM_NAME[team_code], '패배팀': self.MINOR_TEAM_NAME[versus_team]}
        result_list = []

        df_score = self.lab2ai_conn.get_team_score(team_code, game_id)
        df_versus = df_score[df_score['GMKEY'].str.contains("{0}{1}|{1}{0}".format(team_code, versus_team))]
        df_team_score = self.set_wls_score(df_versus, team_code)
        wls_list = df_team_score['WLS'].tolist()

        continue_w = 0
        continue_l = 0
        after_w_game_cnt = 1
        after_d_cnt = 0

        for wls in wls_list:
            if wls == 'W':
                continue_w += 1
            else:
                break

        for wls in wls_list:
            if wls == 'L':
                continue_l += 1
            else:
                break

        for i, wls in enumerate(wls_list):
            if i == 0:
                continue
            if wls != 'W':
                after_w_game_cnt += 1
                if wls == 'D':
                    after_d_cnt += 1
            else:
                break

        versus_continue_dict = data_dict.copy()
        versus_continue_dict[cfg.CATEGORY] = '상대전적_연승패'
        versus_continue_dict['승리수'] = wls_list.count('W')
        versus_continue_dict['패배수'] = wls_list.count('L')
        versus_continue_dict['연승수'] = continue_w
        versus_continue_dict['연패수'] = continue_l
        versus_continue_dict['승_이후_경기수'] = after_w_game_cnt
        versus_continue_dict['승_이후_무승부수'] = after_d_cnt
        # result_list.append(versus_continue_dict)

        # versus_score_dict = data_dict.copy()
        # versus_score_dict[cfg.CATEGORY] = '상대전적_균형'
        # versus_score_dict['상대_패배수'] = wls_list.count('L')
        # versus_score_dict['상대_승리수'] = wls_list.count('W')
        win_kor = "{}승".format(wls_list.count('W')) if wls_list.count('W') > 0 else "무승"
        loss_kor = "{}패".format(wls_list.count('L')) if wls_list.count('L') > 0 else "무패"
        if wls_list.count('D') == 0:
            versus_result = "{} {}".format(win_kor, loss_kor)
        else:
            versus_result = "{} {}무 {}".format(win_kor, wls_list.count('D'), loss_kor)
        versus_continue_dict['전적'] = versus_result
        # result_list.append(versus_score_dict)
        return versus_continue_dict
    # endregion [TEAM EVENT]


