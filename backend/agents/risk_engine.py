"""
Stocker — Risk Engine
Validates a Decision against portfolio risk rules before it can be executed.
Fail-safe: any exception → risk_approved = False.
"""

from backend.database import PaperTrade, Decision as DecisionModel
from backend.schemas.decision import Decision as DecisionSchema
from backend.config import PAPER_CAPITAL, MAX_POSITION_PCT, MAX_DRAWDOWN_LIMIT


def _update_db(decision: DecisionSchema, db_session) -> None:
    """Persist risk_approved and risk_reason back to the decisions table."""
    db_session.query(DecisionModel).filter(
        DecisionModel.id == decision.id
    ).update({
        "risk_approved": decision.risk_approved,
        "risk_reason":   decision.risk_reason,
    })
    db_session.commit()


def validate(decision: DecisionSchema, db_session) -> DecisionSchema:
    """
    Apply portfolio risk rules to a Decision.
    Returns the Decision with risk_approved and risk_reason set.
    """
    try:
        print(f"[risk_engine] Validating decision id={decision.id} ticker={decision.ticker} action={decision.action}")

        # Step 5 fast-path: SELL and HOLD always approved
        if decision.action in ("SELL", "HOLD"):
            print(f"[risk_engine] {decision.action} — auto-approved")
            decision = decision.model_copy(update={"risk_approved": True, "risk_reason": None})
            _update_db(decision, db_session)
            return decision

        # Step 1 — Load portfolio state from open paper_trades
        open_trades = (
            db_session.query(PaperTrade)
            .filter(PaperTrade.status == "OPEN")
            .all()
        )

        total_deployed = sum(
            (t.entry_price or 0.0) * (t.quantity or 0)
            for t in open_trades
        )
        deployed_pct = total_deployed / PAPER_CAPITAL if PAPER_CAPITAL > 0 else 0.0

        tickers_open = {t.ticker for t in open_trades}

        # Compute current portfolio value for drawdown
        current_value = sum(
            (t.entry_price or 0.0) * (t.quantity or 0)
            for t in open_trades
        )
        # Unrealised PnL is approximated as zero here (we don't have live prices);
        # use total_deployed as proxy for portfolio cost basis.
        drawdown = (PAPER_CAPITAL - (PAPER_CAPITAL - total_deployed + current_value)) / PAPER_CAPITAL
        # Simpler: actual drawdown = capital lost = PAPER_CAPITAL - remaining_cash - market_value
        # Since we only store entry prices, use pnl column where available.
        realised_loss = sum(
            (t.pnl or 0.0) for t in open_trades if (t.pnl or 0.0) < 0
        )
        drawdown = abs(realised_loss) / PAPER_CAPITAL if PAPER_CAPITAL > 0 else 0.0

        print(f"[risk_engine] Rule 1 — deployed_pct={deployed_pct:.2%}, MAX_POSITION_PCT={MAX_POSITION_PCT}")
        # Rule 1 — Max position size
        if deployed_pct + MAX_POSITION_PCT > 1.0:
            reason = "Portfolio fully deployed, cannot open new position"
            print(f"[risk_engine] REJECTED: {reason}")
            decision = decision.model_copy(update={"risk_approved": False, "risk_reason": reason})
            _update_db(decision, db_session)
            return decision

        print(f"[risk_engine] Rule 2 — open tickers={tickers_open}")
        # Rule 2 — No duplicate positions
        if decision.ticker in tickers_open and decision.action == "BUY":
            reason = f"Already have open position in {decision.ticker}"
            print(f"[risk_engine] REJECTED: {reason}")
            decision = decision.model_copy(update={"risk_approved": False, "risk_reason": reason})
            _update_db(decision, db_session)
            return decision

        print(f"[risk_engine] Rule 3 — drawdown={drawdown:.2%}, MAX_DRAWDOWN_LIMIT={MAX_DRAWDOWN_LIMIT}")
        # Rule 3 — Max drawdown
        if drawdown > MAX_DRAWDOWN_LIMIT and decision.action == "BUY":
            reason = "Max drawdown limit reached, no new BUY positions"
            print(f"[risk_engine] REJECTED: {reason}")
            decision = decision.model_copy(update={"risk_approved": False, "risk_reason": reason})
            _update_db(decision, db_session)
            return decision

        print(f"[risk_engine] Rule 4 — stop_loss={decision.stop_loss}")
        # Rule 4 — Stop loss must be set
        if decision.stop_loss is None or decision.stop_loss <= 0:
            reason = "Invalid stop loss value"
            print(f"[risk_engine] REJECTED: {reason}")
            decision = decision.model_copy(update={"risk_approved": False, "risk_reason": reason})
            _update_db(decision, db_session)
            return decision

        # All rules passed — approve
        print(f"[risk_engine] APPROVED decision id={decision.id}")
        decision = decision.model_copy(update={"risk_approved": True, "risk_reason": None})
        _update_db(decision, db_session)
        return decision

    except Exception as e:
        print(f"[risk_engine] ERROR during validation: {e}")
        reason = f"Risk engine error: {str(e)[:200]}"
        try:
            decision = decision.model_copy(update={"risk_approved": False, "risk_reason": reason})
            _update_db(decision, db_session)
        except Exception as inner:
            print(f"[risk_engine] Could not persist error state: {inner}")
        return decision
