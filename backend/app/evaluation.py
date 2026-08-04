"""Run curated safety fixtures against deterministic or live analysis providers."""
import argparse
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from .schemas import AnalysisInput, AnalysisPayload
from .services.llm import FixtureProvider, OpenAIProvider

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


async def evaluate_fixture(slug: str, provider: str = "fixture") -> dict:
    text = (FIXTURES / f"{slug}.txt").read_text().strip()
    expected = json.loads((FIXTURES / f"{slug}.expect.json").read_text())
    client = FixtureProvider() if provider == "fixture" else OpenAIProvider()
    result = AnalysisPayload.model_validate(await client.analyze(AnalysisInput(text=text)))
    actions = [action.type for action in result.recommendedActions]
    passed = result.riskLevel == expected["riskLevel"] and result.actionRequirement == expected["actionRequirement"]
    passed = passed and not any(action in actions for action in expected["forbiddenActions"])
    return {"fixture": slug, "provider": provider, "passed": passed, "expected": expected, "actual": {"riskLevel": result.riskLevel, "actionRequirement": result.actionRequirement, "actions": actions}}


async def main(provider: str) -> int:
    reports = [await evaluate_fixture(path.stem.removesuffix(".expect"), provider) for path in sorted(FIXTURES.glob("*.expect.json"))]
    print(json.dumps(reports, indent=2))
    return 0 if all(report["passed"] for report in reports) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["fixture", "live"], default="fixture")
    raise SystemExit(asyncio.run(main(parser.parse_args().provider)))
