from __future__ import annotations

import datetime as dt
import logging
from random import randint
from typing import Self

import pandas as pd

from heats.constants import (
    CF_HEATS_ASSIGNMENTS_WS_NAME,
    CF_HEATS_DONOTASSIGN_WS_NAME,
    CF_HEATS_PREFS_WS_NAME,
    CF_HEATS_PRIORITY_WS_NAME,
    CF_HEATS_SHEET_NAME,
    HEAT_PARAMS_DEFAULT,
    PREFERENCE_START_TIME_WIGGLE_HOURS,
    PREFERENCE_WINDOW_HOURS,
)
from utils.sheets import GoogleSheets

log = logging.getLogger(__name__)


class CFMFHeats:
    def __init__(self, params: dict = HEAT_PARAMS_DEFAULT) -> None:
        self.today = dt.datetime.now(tz=dt.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        self.friday = self.today + dt.timedelta(days=(4 - self.today.weekday()) % 7)
        self.saturday = self.friday + dt.timedelta(days=1)
        self.sunday = self.saturday + dt.timedelta(days=1)
        self.monday = self.sunday + dt.timedelta(days=1)
        self.params = params
        self.reviewed = set()
        self.gs = GoogleSheets()
        self._get_heats_google_data()
        self._get_heats()

    @property
    def luck(self) -> int:
        return len(self.reviewed) + 1

    @property
    def prefs_list(self) -> list[dict]:
        return [
            x
            for x in self.prefs_data
            if x.get("Name") and x.get("Name") not in self.reviewed and x.get("Name") not in self.dna
        ]

    @property
    def override_prefs_list(self) -> list[dict]:
        return [x for x in self.prefs_list if x.get("Name") and x.get("Name") in self.overrides]

    @property
    def vip_prefs_list(self) -> list[dict]:
        return [
            x
            for x in self.prefs_list
            if x.get("Name") and x.get("Name") not in self.overrides and x.get("Name") in self.vips
        ]

    @property
    def assigned_athletes(self) -> list[str]:
        return flatten_list([x["athletes"] for x in self.heats.values()])

    @property
    def unassigned_athletes(self) -> list[str]:
        return [
            str(x.get("Name")) for x in self.prefs_data if x.get("Name") and x.get("Name") not in self.assigned_athletes
        ]

    def _get_heats_google_data(self) -> Self:
        self.prefs_data = self.gs.read_sheets(
            spreadsheet_name=CF_HEATS_SHEET_NAME,
            worksheet_name=CF_HEATS_PREFS_WS_NAME,
        )
        self.priority_data = self.gs.read_sheets(
            spreadsheet_name=CF_HEATS_SHEET_NAME,
            worksheet_name=CF_HEATS_PRIORITY_WS_NAME,
        )
        self.dna_data = self.gs.read_sheets(
            spreadsheet_name=CF_HEATS_SHEET_NAME,
            worksheet_name=CF_HEATS_DONOTASSIGN_WS_NAME,
        )

        self.dna = [x.get("Name") for x in self.dna_data]
        self.overrides = {x.get("Name"): x.get("Override") for x in self.priority_data if x.get("Override") != ""}
        self.vips = [x.get("Name") for x in self.priority_data if x.get("Name")]

        log.info("Number of athletes: %s", len(self.prefs_list))
        return self

    def _get_heats(self) -> Self:
        log.info("Creating heats.")
        heat_interval_mins = self.params.get("heat_interval_mins", 20)
        am_start_time_h, am_start_time_m = str(self.params.get("am_start_time", "06:15")).split(":")
        am_end_time_h, am_end_time_m = str(self.params.get("am_end_time", "09:00")).split(":")
        pm_start_time_h, pm_start_time_m = str(self.params.get("pm_start_time", "17:15")).split(":")
        pm_end_time_h, pm_end_time_m = str(self.params.get("pm_end_time", "20:00")).split(":")

        heat_list = []

        pm_days = [self.friday, self.saturday]

        for day in pm_days:
            # PM Heats
            heat_list.extend(
                create_time_based_heats(
                    day=day,
                    start_time_h=int(pm_start_time_h),
                    start_time_m=int(pm_start_time_m),
                    end_time_h=int(pm_end_time_h),
                    end_time_m=int(pm_end_time_m),
                    interval_m=heat_interval_mins,
                ),
            )

        am_days = [self.saturday]
        if self.params.get("use_sunday"):
            am_days.append(self.sunday)
        if self.params.get("use_monday"):
            am_days.append(self.monday)

        for day in am_days:
            # AM Heats
            heat_list.extend(
                create_time_based_heats(
                    day=day,
                    start_time_h=int(am_start_time_h),
                    start_time_m=int(am_start_time_m),
                    end_time_h=int(am_end_time_h),
                    end_time_m=int(am_end_time_m),
                    interval_m=heat_interval_mins,
                ),
            )

        self.heats = {x: {"athletes": [], "rx": [], "pref": [], "luck": []} for x in sorted(heat_list)}

        return self

    def run_heat_assignments(self) -> Self:
        log.info("Running heat assignments.")
        return self

    def run_hard_overrides(self) -> Self:
        log.info("Assigning hard overrides first.")
        while len(self.override_prefs_list) > 0:
            pref_info = self.override_prefs_list.pop(0)
            name = pref_info.get("Name")
            heat_str = self.overrides[name]
            if name and heat_str:
                self.reviewed.add(name)
                day_str, time_str = heat_str.split(" ")
                time_h_str, time_m_str = time_str.split(":")
                time_h = int(time_h_str) + (12 if "pm" in time_str.casefold() else 0)
                time_m = int(time_m_str.lower().replace("am", "").replace("pm", ""))
                use_dt = self._get_use_datetime(day_str).replace(hour=time_h, minute=time_m)
                if use_dt not in self.heats:
                    log.exception("Error running override for %s. Could not find heat %s", name, heat_str)
                log.info("Assigning override for %s: %s", name, heat_str)
                self.heats[use_dt]["athletes"].append(name)
                self.heats[use_dt]["rx"].append(pref_info["Category"])
                self.heats[use_dt]["pref"].append("1")
                self.heats[use_dt]["luck"].append(str(self.luck))

        return self

    def run_vip_prefs(self) -> Self:
        log.info("Assigning judge/priority preferences next.")
        while len(self.vip_prefs_list) > 0:
            i = randint(0, len(self.vip_prefs_list) - 1)  # noqa: S311
            pref_info = self.vip_prefs_list.pop(i)
            name = pref_info.get("Name")
            if name:
                self.reviewed.add(name)
                self.assign_person_to_heat(pref_info)

        return self

    def run_athlete_prefs(
        self,
        pref_start_time_wiggle_hours: float | None = None,
        pref_window_hours: float | None = None,
    ) -> Self:
        log.info("---------------------------Assigning athletes at random.")
        for name in self.unassigned_athletes:
            if name in self.reviewed:
                self.reviewed.remove(name)
        while len(self.prefs_list) > 0:
            i = randint(0, len(self.prefs_list) - 1)  # noqa: S311
            pref_info = self.prefs_list.pop(i)
            name = pref_info.get("Name")
            if name:
                self.reviewed.add(name)
                self.assign_person_to_heat(
                    pref_info,
                    pref_start_time_wiggle_hours,
                    pref_window_hours,
                )

        return self

    def _get_use_datetime(self, day_str: str) -> dt.datetime:
        """Get datetime object based on day string."""
        day_str_list = ["friday", "saturday", "sunday", "monday"]
        day_dt_list = [self.friday, self.saturday, self.sunday, self.monday]
        return day_dt_list[day_str_list.index(day_str.casefold())]

    def assign_person_to_heat(  # noqa: C901
        self,
        person_info: dict,
        pref_start_time_wiggle_hours: float | None = None,
        pref_window_hours: float | None = None,
    ) -> Self:
        if not pref_start_time_wiggle_hours:
            pref_start_time_wiggle_hours = PREFERENCE_START_TIME_WIGGLE_HOURS
        if not pref_window_hours:
            pref_window_hours = PREFERENCE_WINDOW_HOURS

        max_athletes_per_heat = self.params.get("max_athletes_per_heat", 5)
        max_rx_per_heat = self.params.get("max_rx_per_heat", 2)

        name = person_info["Name"]
        category = person_info["Category"]
        prefs = [person_info.get(f"Preference {x}") for x in range(1, 6)]
        assigned = False
        for idx, pref in enumerate(prefs):
            if not assigned and pref:
                day_str, time_start_str = pref.split(" ")
                use_dt = self._get_use_datetime(day_str)
                pref_start_dt = use_dt.replace(
                    hour=int(time_start_str.replace("am", "").replace("pm", ""))
                    + (12 if "pm" in time_start_str else 0),
                )
                pref_end_dt = pref_start_dt + dt.timedelta(hours=abs(pref_window_hours))
                pref_start_dt = pref_start_dt + dt.timedelta(hours=-1 * abs(pref_start_time_wiggle_hours))
                pref_heats = []
                for k, v in self.heats.items():
                    if pref_start_dt <= k <= pref_end_dt and len(v["athletes"]) < max_athletes_per_heat:
                        if "rx" in category.casefold():
                            if len([x for x in v["rx"] if "rx" in x.casefold()]) < max_rx_per_heat:
                                pref_heats.append(k)
                        else:
                            pref_heats.append(k)

                if len(pref_heats) > 0:
                    assigned_heat = pref_heats[0]
                    self.heats[assigned_heat]["athletes"].append(name)
                    self.heats[assigned_heat]["rx"].append(category)
                    self.heats[assigned_heat]["pref"].append(str(idx + 1))
                    self.heats[assigned_heat]["luck"].append(str(self.luck))
                    assigned = True
                    log.info("Assigned %s to heat %s based on preference %s: %s", name, assigned_heat, idx + 1, pref)

        if not assigned:
            log.warning("Could not assign %s to any heat. Prefs %s", name, prefs)

        return self

    def summarize(self) -> Self:
        log.info("Heats summary: ")
        for k, v in self.heats.items():
            log.info("Heat %s, athletes count %s: %s", k.strftime("%A %H:%M"), len(v["athletes"]), v["athletes"])

        if len(self.unassigned_athletes) > 0:
            log.warning("Unassigned athletes: %s", self.unassigned_athletes)
        else:
            log.info("All athletes assigned.")

        return self

    def publish_heats(self) -> Self:
        max_athletes_per_heat = self.params.get("max_athletes_per_heat", 5)

        df_heats = pd.DataFrame(columns=["Day", "Heat", "Time", "Name", "RX", "Preference #", "Lucky #"])
        df_blank = pd.DataFrame(data={"Day": [""]})

        data = []
        data.append(df_heats)
        data.append(df_blank)
        for heat_i, (k, v) in enumerate(self.heats.items()):
            day = k.strftime("%A")
            time = k.strftime("%I:%M%p")
            if len(v["athletes"]) > 0:
                data.append(pd.DataFrame(data={"Day": [day], "Heat": [f"Heat {heat_i + 1}"], "Time": [time]}))
                for ath, rx, pref, luck in zip(v["athletes"], v["rx"], v["pref"], v["luck"]):
                    data.append(
                        pd.DataFrame(data={"Name": [ath], "RX": [rx], "Preference #": [pref], "Lucky #": [luck]}),
                    )
                if len(v["athletes"]) < max_athletes_per_heat:
                    data.extend([df_blank for _ in range(max_athletes_per_heat - len(v["athletes"]) + 1)])
            data.append(df_blank)

        final_heats = pd.concat(data)
        self.gs.write_df_to_sheets(
            spreadsheet_name=CF_HEATS_SHEET_NAME,
            worksheet_name=CF_HEATS_ASSIGNMENTS_WS_NAME,
            data=final_heats,
        )

        return self


def create_time_based_heats(  # noqa: PLR0913
    day: dt.datetime,
    start_time_h: int,
    start_time_m: int,
    end_time_h: int,
    end_time_m: int,
    interval_m: int,
) -> list[dt.datetime]:
    heats = []
    first_heat = day.replace(hour=start_time_h, minute=start_time_m)
    end_time = day.replace(hour=end_time_h, minute=end_time_m)
    heats.append(first_heat)
    while True:
        heat = heats[-1] + dt.timedelta(minutes=interval_m)
        if heat <= end_time:
            heats.append(heat)
        else:
            break
    return heats


def flatten_list(nested_list: list[list]) -> list:
    return [x for row in nested_list for x in row]
