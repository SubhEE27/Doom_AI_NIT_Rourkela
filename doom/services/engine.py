from __future__ import annotations
from typing import List
from doom.config.settings import DeploymentProfile, PermissionToken, ALLOWED_MANUAL_ENTRY_CATEGORIES
from doom.models.domain import PatientRecord, HospitalAssets, StaffRoster, TriageRecommendation
from doom.core.ingestion import IngestionEngine
from doom.core.stratification import RiskStratifier
from doom.core.scoring import SafetyFloor, TriageModel
from doom.core.routing import ClinicalRouting, TransferPlanner, StaffOrchestrator
from doom.core.layers import PolymorphicController
from doom.core.uncertainty import UncertaintyEstimator
from doom.services.audit import AuditLog

class DoomTriageEngine:
    def __init__(self, deployment_profile: str = DeploymentProfile.MULTISPECIALTY_TERTIARY_CENTER.value):
        if deployment_profile not in {x.value for x in DeploymentProfile}: raise ValueError(f"Unsupported deployment profile: {deployment_profile}")
        self.deployment_profile = deployment_profile
        self.system_permissions = {token.value: False for token in PermissionToken}
        self.ingestion=IngestionEngine(); self.stratifier=RiskStratifier(); self.floor=SafetyFloor(2); self.model=TriageModel(); self.controller=PolymorphicController(); self.routing=ClinicalRouting(); self.transfer=TransferPlanner(); self.staff=StaffOrchestrator(); self.uncertainty=UncertaintyEstimator(); self.audit=AuditLog()

    def request_system_access_permissions(self, tokens_list: List[str]):
        allowed={t.value for t in PermissionToken}
        for token in tokens_list:
            if token not in allowed: raise ValueError(f"Unknown system permission token: {token}")
            self.system_permissions[token]=True
        return dict(self.system_permissions)

    def _assert_infrastructure_permissions(self):
        missing=[k for k,v in self.system_permissions.items() if not v]
        if missing: raise PermissionError("Infrastructure access denied. Authorize: "+", ".join(missing))

    def evaluate(self, patient: PatientRecord, assets: HospitalAssets, staff: StaffRoster):
        self._assert_infrastructure_permissions()
        ing=self.ingestion.normalize(patient); assessment=self.stratifier.assess(patient, ing)
        layers=self.controller.select_layers(assets,staff,patient,self.deployment_profile)
        raw=self.model.predict(patient,assessment); esi,floor=self.floor.apply(raw,assessment)
        uncertainty=self.uncertainty.calculate(patient,assessment)
        if floor: uncertainty=min(.95,uncertainty+.08)
        conf=round((1-uncertainty)*100,1)
        rationale=[
            "Physiology: "+(", ".join(assessment.abnormal_vitals[:2]) if assessment.abnormal_vitals else "no major vital abnormality by demo bands"),
            "Safety signals: "+(", ".join(assessment.critical_flags[:2]) if assessment.critical_flags else "no immediate life-threat flag"),
            "Data quality: "+(", ".join(assessment.missing_critical_fields) if assessment.missing_critical_fields else "available data sufficient for prototype")]
        specialty=self.routing.suggest_specialty(patient); transfer,transfer_text=self.transfer.plan(patient,esi,assets); staff_action=self.staff.orchestrate(patient,esi,staff)
        route=" | ".join([transfer_text]+([f"specialty suggestion: {specialty}"] if specialty else [])+([f"staff orchestration: {staff_action}"] if staff_action else []))
        rec=TriageRecommendation(patient.patient_id,esi,rationale,conf,self.controller.flag(layers),assessment,route,transfer,specialty,round(uncertainty,3),False)
        self.audit.append(patient.patient_id,"AI_ENGINE","TRIAGE_RECOMMENDATION",{"esi":esi,"raw_esi":raw,"floor_applied":floor,"confidence_pct":conf,"operational_layer":rec.operational_layer})
        return rec

    def clinician_override(self, patient, recommendation, clinician_id, new_esi, justification_code, free_text):
        if new_esi not in {1,2,3,4,5}: raise ValueError("new_esi must be 1..5")
        if not clinician_id or not justification_code or len(free_text.strip())<12: raise ValueError("Clinician ID, structured reason and narrative are required")
        self.audit.append(patient.patient_id,f"CLINICIAN:{clinician_id}","TRIAGE_OVERRIDE",{"old_esi":recommendation.esi_level,"new_esi":new_esi,"justification_code":justification_code,"justification_text":free_text})
        return TriageRecommendation(patient.patient_id,new_esi,recommendation.rationale+["Clinician override: "+justification_code],recommendation.confidence_pct,recommendation.operational_layer,recommendation.risk_assessment,recommendation.routing_recommendation,recommendation.transfer_candidate,recommendation.specialist_route,recommendation.uncertainty_indicator,True)

    def process_manual_clinician_entry(self, patient_record, data_category, payload_dict):
        category=data_category.upper()
        if category not in ALLOWED_MANUAL_ENTRY_CATEGORIES: raise ValueError(f"Unsupported manual entry category: {category}")
        if category=="VITAL_SIGNS":
            allowed={"hr","rr","sbp","dbp","spo2"}
            patient_record.vitals.update({k:payload_dict[k] for k in payload_dict if k in allowed})
        elif category=="CLINICAL_NARRATIVE":
            keywords=payload_dict.get("keywords", [])
            if not isinstance(keywords,list): raise TypeError("keywords must be a list")
            patient_record.narrative=(patient_record.narrative+" "+" ".join(map(str,keywords))).strip()
        elif category=="IMAGING_METADATA":
            findings=payload_dict.get("findings", [])
            if not isinstance(findings,list): raise TypeError("findings must be a list")
            patient_record.image_tags.extend(map(str,findings))
        self.audit.append(patient_record.patient_id,"CLINICIAN_UI","MANUAL_DATA_ENTRY",{"category":category,"payload":payload_dict})
        return patient_record

