# Constants for CF Open MF model
CF_LEADERBOARD_URL = "https://c3po.crossfit.com/api/leaderboards/v2/competitions/open/YYYY/leaderboards"


YEAR = 2025
AFFILIATE_ID = 31316
AFFILIATE_NAME = "Crossfit MonkeyFlag"
EVENT_NAMES = {
    1: "25.1",
    2: "25.2",
    3: "25.3",
}

RENDER_CONTEXT = {
    "year": YEAR,
    "affiliate_name": AFFILIATE_NAME,
    "event_names": EVENT_NAMES,
}

TEAM_LOGOS = {
    "1. Toes Too Far": "/static/assets/Toes too far.JPG",
    "2. The Wodfathers": "/static/assets/WODFathers.JPG",
    "3. Barbellgaonkar": "/static/assets/Barbellgaonkar.JPG",
    "4. Ripped Rascals": "/static/assets/Ripped Rascals.png",
    "5. Rowdy Repchicks": "/static/assets/Rowdy Repchicks.JPG",
}

TEAM_INSTA = {
    "1. Toes Too Far": "toestoofar",
    "2. The Wodfathers": "team_wodfathers",
    "3. Barbellgaonkar": "barbellgaonkar",
    "4. Ripped Rascals": "ripped.rascals",
    "5. Rowdy Repchicks": "rowdyrepchicks",
}

TEAM_LEADER_MAP = {
    "TL": 2,
    "C": 1,
}
TEAM_LEADER_REVERSE_MAP = {v: k for k, v in TEAM_LEADER_MAP.items()}

TEAM_ASSIGNMENTS_FILEPATH = "static/team_assignments.csv"
ATTENDANCE_FILEPATH = "static/attendance.csv"
SIDE_CHALLENGE_FILEPATH = "static/side_challenge.csv"
SPIRIT_FILEPATH = "static/spirit.csv"

MF_MASTERS_AGE_CUTOFF = 55
MF_OPEN_AGE_CUTOFF = 35
PARTICIPATION_SCORE = 1
TOP3_SCORE = 3
JUDGE_SCORE = 2
ATTENDANCE_SCORE = 2
DEFAULT_APPRECIATION_SCORE = 10
DEFAULT_SIDE_SCORE = 25

IGNORE_TEAMS = [
    "Short-put Bai-kar",
    "zz",
]

CF_DIVISION_MAP = {
    "1": "Men Open",
    "2": "Women Open",
    "14": "Men 14-15",
    "15": "Women 14-15",
    "16": "Men 16-17",
    "17": "Women 16-17",
    "7": "Men 55-59",
    "8": "Women 55-59",
    "36": "Men 60-64",
    "37": "Women 60-64",
    "40": "Men 65-69",
    "41": "Women 65-69",
    "42": "Men 70+",
    "43": "Women 70+",
}


# Throttle requests
CF_API_REQUEST_THROTTLE_SECONDS = 0
HTTPX_TIMEOUT = 20
