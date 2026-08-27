from doom.models.domain import Layer, PatientRecord, HospitalAssets, StaffRoster
from doom.config.settings import DeploymentProfile

class PolymorphicController:
    def select_layers(self, assets: HospitalAssets, staff: StaffRoster, patient: PatientRecord, profile: str):
        if profile == DeploymentProfile.RURAL_PRIMARY_HEALTH_CENTRE.value:
            return [Layer.L2]
        layers = []
        degraded = (not assets.imaging_online) or (not patient.history_known) or (not patient.files_available)
        layers.append(Layer.L2 if degraded else Layer.L1)
        if assets.bed_occupancy_pct >= 100 or assets.ot_occupancy_pct >= 100:
            layers.append(Layer.L3)
        if staff.night_shift and staff.personnel_deficit:
            layers.append(Layer.L4)
        return layers

    def flag(self, layers):
        return "+".join(x.value.split("-")[0] for x in layers)

