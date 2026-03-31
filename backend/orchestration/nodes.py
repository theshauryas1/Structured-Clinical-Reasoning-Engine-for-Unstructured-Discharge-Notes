from backend.orchestration.policy import (
    decide_post_contradiction,
    decide_post_differential,
    trace_policy_decisions,
)


def plan_after_differential(state: dict) -> dict:
    decisions = decide_post_differential(
        state["timeline"],
        len(state.get("differentials", [])),
    )
    orchestration_trace = list(state.get("orchestration_trace", []))
    orchestration_trace.extend(decisions)
    reasoning_trace = trace_policy_decisions(
        list(state.get("reasoning_trace", [])),
        decisions,
        "policy_agent_post_differential",
    )
    return {
        "orchestration_trace": orchestration_trace,
        "reasoning_trace": reasoning_trace,
    }


def plan_after_contradiction(state: dict) -> dict:
    top_ranking_score = state.get("differentials", [None])[0].ranking_score if state.get("differentials") else 0.0
    decisions = decide_post_contradiction(
        len(state.get("contradictions", [])),
        top_ranking_score,
    )
    orchestration_trace = list(state.get("orchestration_trace", []))
    orchestration_trace.extend(decisions)
    reasoning_trace = trace_policy_decisions(
        list(state.get("reasoning_trace", [])),
        decisions,
        "policy_agent_post_contradiction",
    )
    return {
        "orchestration_trace": orchestration_trace,
        "reasoning_trace": reasoning_trace,
    }
