from typing import Dict, Any, List, Tuple
from datetime import datetime, time
import zoneinfo

def _time_in_window(iso_time: str, tw: Dict[str, Any]) -> Tuple[bool, str]:
    """检查给定时间是否在策略窗口内，支持跨午夜"""
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        tzname = tw.get("tz", "UTC")
        local_dt = dt.astimezone(zoneinfo.ZoneInfo(tzname))
        start_h, start_m = map(int, tw["start"].split(":"))
        end_h, end_m = map(int, tw["end"].split(":"))
        t_start = time(start_h, start_m)
        t_end = time(end_h, end_m)
        now_t = local_dt.time()
        if t_start <= t_end:
            ok = t_start <= now_t <= t_end
        else:
            # 跨午夜窗口，如 22:00-06:00
            ok = now_t >= t_start or now_t <= t_end
        return ok, f"time {now_t} in window {t_start}-{t_end} {tzname}"
    except Exception as e:
        return False, f"time check error: {e}"

def evaluate_against_policies(policies: List[Dict[str, Any]], login: Dict[str, Any]):
    """
    简化合并逻辑：
      - 先收集所有命中的策略
      - 冲突时：block > allow；若都 allow，看是否有要求 MFA / Reset，取更严格
    """
    matched = []
    explanations = []

    for p in policies:
        if not p.get("enabled", True):
            continue

        cond = p.get("conditions", {})
        ok = True
        local_reasons = []

        # 用户/组
        cond_users = cond.get("users")
        if cond_users:
            user = login.get("user")
            groups = set(login.get("groups", []))
            need = False
            for u in cond_users:
                if u.startswith("group:"):
                    if u.split(":",1)[1] in groups:
                        need = True
                elif u.startswith("user:"):
                    if u.split(":",1)[1] == user:
                        need = True
            if not need:
                ok = False
            else:
                local_reasons.append("user/group matched")

        # 地理
        cond_locs = cond.get("locations")
        if ok and cond_locs:
            if login.get("geo") not in cond_locs:
                ok = False
            else:
                local_reasons.append(f"geo {login.get('geo')} matched")

        # 应用
        cond_apps = cond.get("apps")
        if ok and cond_apps:
            if login.get("app") not in cond_apps:
                ok = False
            else:
                local_reasons.append(f"app {login.get('app')} matched")

        # 时间窗口
        tw = cond.get("timeWindow")
        if ok and tw:
            inwin, reason = _time_in_window(login.get("time"), tw)
            if not inwin:
                ok = False
            else:
                local_reasons.append(reason)

        # 设备合规
        dc = cond.get("deviceCompliance", "any")
        if ok and dc != "any":
            compliant = bool(login.get("device", {}).get("compliant", False))
            if (dc == "compliant" and not compliant) or (dc == "non_compliant" and compliant):
                ok = False
            else:
                local_reasons.append(f"device compliance {compliant} ok for {dc}")

        # 风险
        sr_need = cond.get("signInRisk", "low_or_none")
        sr = login.get("risk", {}).get("signInRisk", "none")
        rank = {"none":0, "low":1, "medium":2, "high":3}
        if ok:
            if sr_need == "low_or_none":
                if rank[sr] > 1:  # medium/high 不行
                    ok = False
                else:
                    local_reasons.append(f"sign-in risk {sr} accepted")
            else:
                # 精确匹配（可按需放宽）
                if sr != sr_need:
                    ok = False
                else:
                    local_reasons.append(f"sign-in risk == {sr}")

        if ok:
            matched.append(p)
            explanations.append(f"[{p.get('name')}] " + "; ".join(local_reasons))

    # 合并决策
    if not matched:
        return {
            "decision": "block",
            "requirements": {"mfa": True, "passwordReset": False},
            "matchedPolicies": [],
            "explanations": explanations + ["no policy matched → default block + require MFA"]
        }

    # 只要有 block，整体 block
    for p in matched:
        if p["actions"]["effect"] == "block":
            return {
                "decision": "block",
                "requirements": {"mfa": False, "passwordReset": p["actions"].get("passwordReset", False)},
                "matchedPolicies": [m["name"] for m in matched],
                "explanations": explanations + ["a blocking policy matched"]
            }

    # 全是 allow：取最严格要求
    mfa = any(p["actions"].get("mfa", False) for p in matched)
    pwd = any(p["actions"].get("passwordReset", False) for p in matched)
    return {
        "decision": "allow",
        "requirements": {"mfa": mfa, "passwordReset": pwd},
        "matchedPolicies": [m["name"] for m in matched],
        "explanations": explanations
    }
