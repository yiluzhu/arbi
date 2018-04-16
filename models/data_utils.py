from arbi.constants import ARBI_SUMMARY_HEADER


def get_sport_type(info):
    return {True: 'basketball', False: 'football'}[is_match_basketball(info)]


def is_match_basketball(info):
    league_name = info['league_name'].upper()
    return league_name.endswith('[B]') or league_name.startswith('NBA ') or \
           league_name in ['WNBA', 'NBA', 'NCAA', 'CBA'] or info['home_team_name'].upper().endswith('[B]') or \
           info['away_team_name'].upper().endswith('[B]')


def log_opps_details(log, arbi_opps):
    for opp in arbi_opps:
        opp_summary = {name: (content.encode('utf8') if name in ['League CN', 'Home CN', 'Away CN'] else content)
                       for name, content in zip(ARBI_SUMMARY_HEADER, opp.get_summary())}
        log.info(opp_summary)
