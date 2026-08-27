from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    if mods["batch"] is None:
        from .common import skip_case
        return [skip_case("H05", "Full ER/OT capacity and transfer routing", "BatchTriageService is not present.")]

    def transfer_case():
        engine = new_engine(mods)
        authorize(engine)
        assets = make_assets(mods, emergency_rooms_total=3, emergency_rooms_available=0, operating_theatres_total=3, operating_theatres_available=0, bed_occupancy_pct=100, ot_occupancy_pct=100, volume=300, normal_volume=100, ed_wait=140)
        staff = make_staff(mods, shift="night", emergency_physicians=1, nurses=2)
        pts = [
            make_patient(mods, "T1", 34, "M", "ankle fracture", "stable orthopedic fracture", vitals={"hr":88,"rr":17,"sbp":118,"dbp":76,"spo2":98}),
            make_patient(mods, "T2", 28, "F", "minor fracture", "stable orthopedic fracture", vitals={"hr":82,"rr":16,"sbp":120,"dbp":75,"spo2":99}),
            make_patient(mods, "T3", 45, "M", "chest pain", "high risk chest pain", vitals={"hr":118,"rr":26,"sbp":88,"dbp":54,"spo2":92}),
        ]
        result = mods["batch"].BatchTriageService(engine).evaluate_batch(pts, assets, staff)
        high = [r for r in result.recommendations if r.esi_level <= 2]
        stable = [r for r in result.recommendations if r.esi_level >= 3]
        no_auto_high_transfer = all(not r.transfer_candidate for r in high)
        return (no_auto_high_transfer and any(r.transfer_candidate for r in stable), f"ER/OT full; high-acuity auto-transfer={not no_auto_high_transfer}; stable transfer candidates={[r.patient_id for r in stable if r.transfer_candidate]}")
    return [run_case("H05", "Full ER/OT capacity with safe nearby transfer", transfer_case, "High-acuity patients stay local unless clinician-managed; stable candidates may be routed when receiving capacity and time-to-treatment favor transfer.")]


