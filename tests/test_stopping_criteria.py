from browser_agent.config import Settings
from browser_agent.core.state import AgentState, StepRecord
from browser_agent.core.stopping_criteria import StopReason, StoppingCriteria
from browser_agent.utils.cost_tracker import CostTracker


def make(**kw):
    s = Settings(**kw)
    return StoppingCriteria(s), CostTracker(3.0, 15.0)


def test_max_steps():
    sc, cost = make(max_steps=2)
    st = AgentState(task="t")
    st.steps = [StepRecord(i, "", "click", {}, "", True, "") for i in (1, 2)]
    assert sc.check(st, cost) == StopReason.MAX_STEPS


def test_loop_detection():
    sc, cost = make(loop_repeat_limit=3)
    st = AgentState(task="t", signatures=["a", "b", "x", "x", "x"])
    assert sc.repeat_count(st) == 3
    assert sc.check(st, cost) == StopReason.LOOP


def test_cost_cap_and_failures():
    sc, cost = make(max_cost_usd=0.01, max_consecutive_failures=2)
    cost.input_tokens = 10_000_000
    assert sc.check(AgentState(task="t"), cost) == StopReason.COST_CAP
    sc2, cost2 = make(max_consecutive_failures=2)
    assert sc2.check(AgentState(task="t", consecutive_failures=2), cost2) == StopReason.FAILURES


def test_no_stop():
    sc, cost = make()
    assert sc.check(AgentState(task="t"), cost) is None