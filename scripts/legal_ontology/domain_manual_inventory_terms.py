from __future__ import annotations

import re
from typing import Final

FINANCIAL_IDENTIFIER_TERMS: Final = ("계좌", "은행", "입금", "송금")
ARTICLE_RE: Final = re.compile(r"제\s*\d+\s*조(?:의\s*\d+)?")
SENSITIVE_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    "resident_registration": re.compile(r"\b\d{6}-\d{7}\b"),
    "phone": re.compile(r"(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}"),
    "financial_identifier": re.compile("(?:" + "|".join(FINANCIAL_IDENTIFIER_TERMS) + r").{0,24}" + r"\d"),
    "long_digit_sequence": re.compile(r"\b\d{10,16}\b"),
}
LAW_NAMES: Final = (
    "민사집행법",
    "민법",
    "채권의 공정한 추심에 관한 법률",
    "개인채무자보호법",
    "채무자 회생 및 파산에 관한 법률",
    "신용정보의 이용 및 보호에 관한 법률",
)
WORKFLOW_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "intake": ("사건 기본정보", "처음 받았을 때", "첫 분류"),
    "identity_evidence_package": ("증빙 패키지", "초본", "주소 이력", "신분"),
    "limitation_review": ("시효", "소멸시효", "시효위험"),
    "title_acquisition": ("집행권원", "지급명령", "민사소송", "공정증서"),
    "service_finality_execution_clause": ("송달", "확정", "집행문"),
    "voluntary_recovery": ("임의변제", "일부변제", "분할납부", "채무승인"),
    "provisional_remedy": ("가압류", "가처분", "보전처분"),
    "asset_discovery": ("정보 단서", "재산조회", "등기부", "등록부"),
    "execution_route_selection": ("압류", "추심명령", "전부명령", "루트별"),
    "insolvency_discharge_review": ("회생", "파산", "면책"),
    "monitoring_retry": ("모니터링", "재시도", "장기거주"),
    "closure": ("종결", "회수불능", "최종 운영"),
}
FACT_HANDLE_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "claim.basic_info": ("사건 기본정보", "채권자", "채무자"),
    "claim.evidence_package": ("증빙", "계약서", "판결문", "지급명령"),
    "claim.limitation.dates": ("시효", "확정일", "변제일", "승인일"),
    "claim.enforcement_title.status": ("집행권원", "공정증서", "판결", "지급명령"),
    "claim.service_finality_execution_clause": ("송달", "확정", "집행문"),
    "claim.ledger.amounts": ("원금", "이자", "비용", "변제"),
    "debtor.asset_hints": ("은행", "급여", "부동산", "자동차", "보험"),
    "debtor.insolvency_status": ("회생", "파산", "면책"),
    "governance.stopgate_status": ("압류금지", "컴플라이언스", "보류", "금지"),
}
RISK_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "limitation_risk": ("시효위험", "소멸시효", "시효완성"),
    "exempt_property": ("압류금지", "복지급여", "생계"),
    "insolvency_discharge": ("면책", "개인회생", "파산"),
    "missing_title_or_service": ("집행권원 없음", "송달", "확정", "집행문"),
    "ambiguous_balance": ("원금", "이자", "비용", "상계", "충당"),
    "unsupported_contact": ("채권추심", "컴플라이언스", "연락"),
}
FINANCE_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "principal": ("원금", "잔원금"),
    "interest": ("이자", "연체이자", "지연손해금"),
    "enforcement_costs": ("집행비용", "법조치 비용", "비용"),
    "payments": ("변제", "일부변제", "분할납부"),
    "payment_allocation": ("변제충당", "충당", "상계"),
    "remaining_balance": ("잔액", "남은 채권", "회수금"),
    "assignment_succession": ("채권양도", "승계"),
    "surety_subrogation": ("보증", "구상", "대위"),
}
SCORING_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "legal_readiness": ("집행권원", "송달", "확정", "집행문"),
    "asset_signal_strength": ("은행 단서", "급여", "부동산", "매출"),
    "recovery_expected_value": ("회수 가능성", "예상 회수", "스코어링"),
    "risk_penalty": ("시효위험", "면책", "압류금지", "보류"),
    "time_to_action": ("우선순위", "빠른", "다음 조치"),
}
ACTION_PACKET_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "evidence_request": ("증빙", "확인", "서류"),
    "legal_action_review": ("지급명령", "민사소송", "가압류", "압류"),
    "finance_review": ("원금", "이자", "비용", "변제"),
    "contact_review": ("임의변제", "분할납부", "채무승인"),
    "monitoring_retry": ("재산조회", "모니터링", "재시도"),
    "insolvency_recovery_review": ("회생", "파산", "면책"),
}
