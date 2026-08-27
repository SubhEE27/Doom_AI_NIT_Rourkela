from collections.abc import Iterable

class ArrivalStream:
    """Processes whatever iterable arrives; no fixed patient count."""
    def __init__(self, source: Iterable): self.source = source
    def consume(self, handler): return [handler(patient) for patient in self.source]

class HistoryMixMonitor:
    def inspect(self, patients):
        total=len(patients); with_history=sum(1 for p in patients if p.history_known and p.files_available); without_history=total-with_history
        return {"total":total,"with_history":with_history,"without_history":without_history,"with_history_pct":round(with_history/max(total,1)*100,1),"without_history_pct":round(without_history/max(total,1)*100,1)}

