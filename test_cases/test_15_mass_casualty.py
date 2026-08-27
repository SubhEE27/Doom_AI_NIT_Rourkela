from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    if mods["batch"] is None:
        from .common import skip_case
        return [skip_case("H15", "Mass-casualty ten-patient surge", "BatchTriageService is not present.")]

    def mci():
        engine = new_engine(mods)
        authorize(engine)
        assets = make_assets(mods, emergency_rooms_total=3, emergency_rooms_available=0, operating_theatres_total=3, operating_theatres_available=0, volume=300, normal_volume=100, bed_occupancy_pct=100, ot_occupancy_pct=100, ed_wait=140)
        staff = make_staff(mods, shift="night", emergency_physicians=3, nurses=3, specialists={"trauma surgery":1,"orthopaedics":1,"generalist":1,"critical care":1})
        patients = [
            make_patient(mods,"MCI01",36,"M","trauma","high-speed collision, suspected internal bleeding",vitals={"hr":132,"rr":30,"sbp":82,"dbp":50,"spo2":92}),
            make_patient(mods,"MCI02",52,"F","trauma","blunt abdominal trauma, dizziness",vitals={"hr":126,"rr":28,"sbp":86,"dbp":52,"spo2":94}),
            make_patient(mods,"MCI03",41,"M","trauma","facial burns and breathing difficulty",vitals={"hr":120,"rr":36,"sbp":98,"dbp":60,"spo2":88}),
            make_patient(mods,"MCI04",29,"M","fracture","closed tibia fracture, stable",vitals={"hr":92,"rr":18,"sbp":122,"dbp":76,"spo2":98}),
            make_patient(mods,"MCI05",33,"F","fracture","wrist fracture, stable",vitals={"hr":84,"rr":16,"sbp":118,"dbp":74,"spo2":99}),
            make_patient(mods,"MCI06",47,"M","laceration","superficial bleeding controlled",vitals={"hr":82,"rr":16,"sbp":124,"dbp":78,"spo2":99}),
            make_patient(mods,"MCI07",63,"F","back pain","minor trauma, ambulatory",vitals={"hr":86,"rr":17,"sbp":130,"dbp":80,"spo2":98}),
            make_patient(mods,"MCI08",22,"M","ankle sprain","stable and ambulatory",vitals={"hr":78,"rr":15,"sbp":118,"dbp":72,"spo2":99}),
            make_patient(mods,"MCI09",31,"F","minor burn","small superficial burn",vitals={"hr":90,"rr":17,"sbp":120,"dbp":76,"spo2":98}),
            make_patient(mods,"MCI10",58,"M","shoulder pain","minor trauma, stable",vitals={"hr":88,"rr":18,"sbp":126,"dbp":78,"spo2":98}),
        ]
        result = mods["batch"].BatchTriageService(engine).evaluate_batch(patients, assets, staff)
        ranks = [r.rank for r in result.recommendations]
        esi = [r.esi_level for r in result.recommendations]
        full = result.rooms_full and result.ots_full
        no_high_auto_transfer = all(not r.transfer_candidate for r in result.recommendations if r.esi_level<=2)
        return (len(result.recommendations)==10 and ranks==list(range(1,11)) and all(1<=x<=5 for x in esi) and full and no_high_auto_transfer, f"10 simultaneous MCI arrivals ranked; ESI order={esi}; ER/OT full={full}; high-acuity auto-transfer blocked={no_high_auto_transfer}.")
    return [run_case("H15", "10-patient mass-casualty surge with 3 ER beds / 3 OTs", mci, "Demonstrates simultaneous arrivals, ranking, scarce-resource routing, specialist pressure and safe transfer/holding behavior.")]


