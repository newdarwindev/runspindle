import hashlib
import html
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docs.marketing.paper_source import verify_paper_source
    from docs.marketing.presentation_source import verify_presentation_source
    from docs.marketing.refinery_mirror import verify_refinery_mirror
else:
    # Resolve the guards beside this script, including in isolated test copies.
    from paper_source import verify_paper_source
    from presentation_source import verify_presentation_source
    from refinery_mirror import verify_refinery_mirror


def verify_vision_mirror(folder: Path) -> None:
    """Verify recorded canonical bytes before any generator writes.

    This checks local integrity against reviewed Console pins, not remote
    availability, visual acceptance, or runtime behavior.
    """
    entries = json.loads((folder / "artifacts.json").read_text())["artifacts"]
    commits: set[str] = set()
    for name in (
        "vision.html",
        "LICENSE-SRC-010.txt",
        "SRC-010-lift.json",
        "SRC-010-validation.md",
    ):
        matches = [item for item in entries if item["path"] == "docs/marketing/" + name]
        if len(matches) != 1:
            raise ValueError("Missing or duplicate SRC-010 mirror entry: " + name)
        item = matches[0]
        canonical = item.get("canonical", {})
        path = folder / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or symlink SRC-010 mirror: " + name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if (
            "SRC-010" not in item["source_ids"]
            or canonical.get("repository") != "newdarwindev/runspindle-console"
            or canonical.get("path") != "docs/product/" + name
            or not re.fullmatch(r"[0-9a-f]{40}", canonical.get("commit", ""))
            or digest != item.get("sha256")
            or digest != canonical.get("sha256")
        ):
            raise ValueError("SRC-010 canonical mirror mismatch: " + name)
        commits.add(canonical["commit"])
        if name == "vision.html" and item.get("verification") != {
            "static_integrity": "passed",
            "visual_keyboard_zoom": "blocked",
            "runtime": "not_implemented",
        }:
            raise ValueError("SRC-010 visual acceptance remains blocked")
        if (
            name == "LICENSE-SRC-010.txt"
            and digest
            != "fcf64df3e04554728cc4f082f244fa3dc672c2c6368f22360e6491a113204895"
        ):
            raise ValueError("SRC-010 MIT notice changed")
    if len(commits) != 1:
        raise ValueError("SRC-010 mirrors must share one canonical revision")


P = Path(__file__).resolve().parent
verify_vision_mirror(P)
verify_refinery_mirror(P)
verify_paper_source(P)
verify_presentation_source(P)
P.mkdir(exist_ok=True)
sections = [
    (
        "A bounded system for authorized work",
        """Runspindle is a proposed distribution of cooperating components for agent-assisted work. Its aim is to make task boundaries, human control, evidence, and recovery explicit. The current deliverable is a scaffold and design specification. It is not an operating service, a production deployment, or a measured improvement over a native agent product.
A task begins with a defined outcome, accountable owner, permitted sources and actions, and stop conditions. An agent's ability to perform an action is not authority to perform it. Scope changes and consequential actions require the applicable approval. Product policy and legal constraints remain in force; the architecture is not a mechanism for bypassing them.""",
    ),
    (
        "Why a specialist harness might help",
        """A general-purpose agent can leave work unfinished even when a bounded, permitted path exists. The useful engineering question is whether a narrow integration can improve verified completion without expanding authority. Additional prompting, retries, and tool calls can also increase cost or create duplicate external effects. Runspindle therefore treats completion, authorization, and recovery as separate things to verify.
A future comparison should hold the task and permission boundary constant. Native assistance, expert-guided assistance, and the proposed harness should receive matched tasks. Count failures, human intervention, and uncertain results, rather than reporting only successful examples. No such comparative Runspindle study has been completed.""",
    ),
    (
        "Seven components with separate responsibilities",
        """Core is planned in Rust with Temporal for durable task state, approval waits, and explicit retry and reconciliation decisions. Host is the proposed native Codex integration and owns host/session identity checks. Browser is planned around OpenBao secret references, PinchTab actions, and a KasmVNC human view of the same browser.
Tether is intended to adapt the existing Tether Slack integration, with verified actors and bounded routing rather than granting authority from message arrival. Refinery is the proposed Python DSPy experiment layer. Console is intended to show actual fleet observations, including their age and unknown states; the current scaffold has no connected fleet. Platform owns the proposed distribution manifests, release packaging, development environment, and deployment gates.
These are component contracts, not assertions that their integrations work. Naming a technology does not establish compatibility, availability, or a security guarantee.""",
    ),
    (
        "Browser control and human takeover",
        """The intended browser model is one isolated account context, one headed browser, and one current controller. A broker would bind commands to account, task, actor, and lease epoch. PinchTab would provide the action interface. KasmVNC passive viewing is proposed as a separate, authorized read-only mode that grants no input control. Interactive takeover would require a fresh fenced control lease on the same browser. A handoff must invalidate old commands and revoke existing input and streams before granting a new epoch.
OpenBao is proposed for secret references and controlled credential access. Credentials and browser profiles must not enter logs, public artifacts, or model evaluation datasets. Temporal records durable intent; it cannot by itself fence browser input or prove whether a website accepted a submission. After an ambiguous external action, the workflow must reconcile observable state before retrying. These properties still require Runspindle integration and adversarial tests.""",
    ),
    (
        "Refinement without default collection",
        """The proposed refinery begins only with an explicitly selected workflow and authorized examples. Review and redaction precede dataset entry. Dataset versions should retain source permission, adjudication, group identifiers, and stable train, validation, and held-out splits. Related examples must remain in the same split to reduce leakage. Proposed feedback records would bind attributable reactions or replies to the exact output and its version. Task-specific automatic gold rules may admit examples only under explicit criteria; conflicting signals must be quarantined for adjudication. Gold eligibility is separate from candidate release approval.
Python DSPy candidates would be compared with a baseline under a fixed task definition and evaluation budget. Quality, safety failures, latency, human repair, and total cost belong in the comparison. Experiments cannot promote themselves. A versioned release needs threshold evidence, human authorization, and a rollback reference. No live collection, provider invocation, training, promotion, or saving is claimed.""",
    ),
    (
        "Economics of accepted work",
        """SRC-005 is the selected economics section within the SRC-002 paper bundle. This original adaptation is not a historical rebuild or measured economics. Define the workload, accounting period, currency, task boundary and acceptance/permission rules before comparing alternatives. A is the count of distinct terminal outcomes that meet both the declared goal and authorization rules. Retries and unverified outputs are not accepted outcomes; failed, rejected and unauthorized attempts still incur costs.

Accounting identity: C = M + T + H + V + K + R + F; U = C / A for A > 0. M is model expense, T tools/infrastructure, H human operation, V verification, K maintenance, R recovery/repair, and F allocated fixed integration, onboarding, exception-design and initial evaluation expense. The seven disjoint period totals use one currency; U is currency per accepted authorized completion. Assign each cost once: for example, verification labor belongs in V rather than also H, and initial evaluation in F rather than also V. State allocation periods and avoid hiding setup expense outside the comparison. With A = 0, U is undefined even if C = 0; report incurred C and zero completions. Unknown inputs remain unknown, not zero. The executable model stores costs in millionths of a currency unit, so its exact conversion is U = C_micro / (1,000,000 * A).

Compare native assistance, expert-guided assistance and a specialist harness on matched task families with the same permission and acceptance rules. Report cost alongside acceptance, quality, safety, latency and human repair; a cheaper attempt need not produce cheaper accepted work. More model use might reduce repair, but only observation can establish that tradeoff. Reference [1] motivates evaluating cost together with accuracy; it supplies no Runspindle return-on-investment estimate.

Fixed-cost sensitivity: for A > 0, the identity can be regrouped as U = F / A + (C - F) / A. This is accounting, not a volume forecast: recurring costs and acceptance can change with workload. Rare tasks can favor manual help because integration and evaluation must be funded before useful output. Report the assumed workload mix, period, labor rates, acceptance rate and maintenance cadence. Include all failures and cleanup on both sides. The source's schematic amortization diagram is excluded; its idea is represented here without curves or an estimated crossing. A specialist may remain more expensive at every volume. No measured break-even point is known.

Synthetic illustration only: the original executable example assumes ten attempts and total cost of 20 USD, including 10 USD fixed integration. Holding every cost fixed while varying A through 0, 1, 5 and 10 gives undefined, 20, 4 and 2 USD per accepted authorized completion. This isolates denominator sensitivity and neither predicts acceptance nor holds in general when volume changes. More generally, at fixed positive A an added cost dC raises U by dC / A; at fixed C, lowering A between positive values raises U when C > 0. Stress maintenance, repair, setup allocation and completion assumptions together before a real comparison. No measured input, savings or profitability follows from these invented totals.

Customer value and vendor revenue are different quantities. Measure active effort, elapsed time, rework, audit usefulness and access to otherwise impractical tasks separately; released time does not automatically reduce cash spending. Subscription, integration and completion fees allocate different risks. An attempt fee can reward extra activity, whereas an accepted-outcome fee can encourage easy-task selection or disagreement about verification. Specify the acceptance test, eligible workload, exceptions and dispute process in the commercial agreement. This is a comparison of incentives, not a Runspindle offer, price schedule or forecast.

Provider change can remove a specialist's advantage through stronger models, built-in workflow features, improved platform APIs or incumbent products. In one engineering report, Anthropic describes removing context-reset machinery after moving from Sonnet 4.5 to Opus 4.5 [2]. That is a vendor's observation in a particular application-development setting, not a general prediction. The source's opportunity diagram is excluded; retain three qualitative scenarios instead: domain-specific value persists, the product becomes a narrower complement, or the gap closes and value erodes. Access restrictions could also eliminate a niche. These are possibilities without probabilities, calibrated axes or estimated trajectories.

Potential enduring assets include a permissioned task corpus, domain acceptance tests, reliable integration, skilled exception handling and customer reach. None ensures a lasting advantage. Evaluate against the current native product, then rerun the same held-out task families after material provider or platform changes, documenting versions and any task changes. If a previous gain disappears, reassess the service rather than carrying the old result forward. Additional generic prompting alone does not establish durable value.

Complementary investment and delayed benefits: the productivity J-curve literature [3] explains how intangible investment can precede gains visible in ordinary productivity measures. Track integration effort and outcomes over time instead of declaring success after one completed task. This is neither a promise of eventual gains nor a reason to omit setup costs. Runspindle has no measured prices, costs, refusal rates, savings, break-even point or market size. Historical claims are not Runspindle evidence. Rights to original prose and diagrams remain unresolved; the selected concepts are accounted for by original adaptation and explicit exclusions, while migration and native TeX validation remain partial.

[1] Sayash Kapoor, Benedikt Stroebl, Zachary S. Siegel, Nitya Nadgir and Arvind Narayanan. AI Agents That Matter (2024), arXiv:2407.01502. https://arxiv.org/abs/2407.01502 .

[2] Prithvi Rajasekaran. Harness design for long-running application development. Anthropic, March 24, 2026. https://www.anthropic.com/research/harness-design-long-running-apps . One vendor engineering observation; no general obsolescence forecast.

[3] Erik Brynjolfsson, Daniel Rock and Chad Syverson. The Productivity J-Curve: How Intangibles Complement General Purpose Technologies. NBER Working Paper 25148, October 2018, revised January 2020. https://www.nber.org/papers/w25148 . Complementary investment and measurement timing, not guaranteed profitability.""",
    ),
    (
        "Fleet evidence and uncertainty",
        """A fleet view should distinguish a planned component, an observed process, a managed session, and a verified terminal result. Every observation needs a timestamp, source, and freshness policy. Missing updates mean unknown state, not automatic proof of failure. Control actions need a verified binding to the intended host, repository, process, and session.
Console should eventually render those actual observations rather than synthetic success indicators. Tether messages may link to a bounded task or evidence record, but message delivery is not execution completion. A stale route, recycled process identifier, or disconnected host must not silently redirect an action. Standard Collectors and Langfuse integration are proposed for correlated task, session, trace, and output identity with readback verification. Masking coverage remains unresolved across those paths; no complete redaction guarantee is claimed. The scaffold does not yet collect or render live observations.""",
    ),
    (
        "Evaluation and release gates",
        """Development validation should test contracts and synthetic fixtures first: lease fencing, isolation, duplicate requests, restart recovery, permission changes, cancellation, stream revocation, and unknown external outcomes. Integration tests then need pinned component versions and permissioned environments. No source repository's historical test result transfers automatically to the new system.
Production readiness requires independently evidenced secrets management, authenticated routing, monitoring, rollback, dependency review, and operator acceptance. Packaging a manifest is not deployment; a passing stub test is not proof of a live system. Development and production deployment remain planned. The distribution must fail closed when prerequisites or authorization are missing.""",
    ),
    (
        "Claims, sources, and open questions",
        """This migration adapts selected concepts under opaque source identifiers SRC-002, SRC-013, and SRC-009. These are partial migrations and newly written adaptations, not faithful re-renders. Historical PDFs are preserved separately and are not Runspindle builds. Detailed source provenance and review records are kept outside the public candidate. Source selection does not establish a new project license or third-party endorsement.
The next useful evidence is a reproducible, permissioned end-to-end task that traverses the component boundaries and demonstrates recovery from an uncertain result. Until then, the materials describe a research and engineering plan. Open questions include native session integration, browser lifecycle compatibility, least-privilege secret delivery, evaluation validity, release reproducibility, and operational cost.""",
    ),
]
# SRC-002 TeX is independently authored; its old PDF is preserved, not regenerated.
(P / "economics.md").write_text(
    "# Runspindle economics\n\nStatus: proposed accounting model; no measured results.\n\n"
    + sections[5][1]
    + "\n\nSource concept: SRC-005.\n"
    + "\nExecutable accounting and synthetic sensitivity: [model specification](economics-model.md); run `python3 tools/economics.py` from the repository root. This original model is not measured evidence. See [SRC-005 disposition](SRC-005-disposition.json) and [review and validation](SRC-005-review.md) for adapted concepts, excluded expression and remaining limits.\n"
)
(P / "overview.md").write_text(
    "# Runspindle\n\n" + "\n\n".join("## " + h + "\n\n" + t for h, t in sections) + "\n"
)
style = "body{max-width:72rem;margin:auto;padding:3rem 1.5rem;font:18px/1.65 system-ui;color:#183247;background:#f7fafc}h1{font-size:3rem;line-height:1.1}h2{line-height:1.25;margin-top:2.6rem}p{max-width:78ch}.badge{color:#6b3600;background:#fff0d3;padding:1rem;border-radius:.6rem}a{color:#075985}nav{display:flex;gap:1rem;flex-wrap:wrap}footer{border-top:1px solid #b8c8d2;margin-top:3rem;padding-top:1rem}"


def page(name: str, title: str, parts: list[tuple[str, str]]) -> None:
    b = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'
        + title
        + "</title><style>"
        + style
        + '</style><body><nav><a href="index.html">Overview</a><a href="browser.html">Browser</a><a href="vision.html">Refinery</a></nav><main><h1>'
        + title
        + '</h1><p class="badge">Design scaffold. Integrations and deployments are planned. No measured savings or live fleet is claimed.</p>'
    )
    for h, t in parts:
        b += (
            "<section><h2>"
            + html.escape(h)
            + "</h2>"
            + "".join("<p>" + html.escape(x) + "</p>" for x in t.split("\n"))
            + "</section>"
        )
    b += "</main><footer>Runspindle design materials. Source concepts: SRC-002, SRC-013, SRC-009. Historical artifacts are not new builds. Third-party products retain their own names and licenses.</footer></body></html>"
    (P / name).write_text(b)


page("index.html", "Runspindle", [sections[i] for i in [0, 2, 6, 7, 8]])
page("browser.html", "Runspindle Browser", [sections[i] for i in [0, 3, 6, 7]])


# Authored decks and all three preserved old PDFs are read-only to this generator.
(P / "THIRD_PARTY_NOTICES.md").write_text("""# Third-party notices and source status

Runspindle names Rust, Temporal, Codex, OpenBao, PinchTab, KasmVNC, Slack, Python, DSPy, and Langfuse only to identify proposed integrations. No endorsement is implied, and this document does not relicense those products.

SRC-010 and SRC-013 selected source material carries the MIT notice: Copyright (c) 2026 newdarwindev. The complete original notice is retained separately in LICENSE-SRC-010.txt and LICENSE-SRC-013.txt. SRC-010 is the selected standalone vision page; its inline styles and adapted narrative require no additional rendering assets, scripts, fonts, or packages. Linked historical documents are navigation, not dependencies, and are not imported by this lift. The permission notice applies to that source material and its adapted portions, not automatically to this entire distribution.

No project license was found for SRC-002 or SRC-009 during source review. No license is invented or assigned to them here. Detailed provenance and original artifacts remain in restricted migration records outside this public candidate. A publisher must resolve the rights to any retained expression before release.

The SRC-013 paper is a byte-preserved, compiled adaptation with eight cleared historical figures. See [SRC-013 notices](SRC-013-NOTICES.md) for the separate Latin Modern font notice and [source disposition](source-disposition.json) for scope. The full historical paper, unselected code, Git history and private operational evidence are not republished. Other documents are original conceptual adaptations, not fresh verification of historical claims.

SRC-002 now has a full nine-section original editable research proposal and five original schematic inputs. No historical prose, diagram expression, coordinates, style or binary is imported. Its unchanged older ReportLab PDF is not a rendering of the new source. Native compilation and page review remain unperformed. Citation attribution is not a license to reproduce source expression. See SRC-002-disposition.json and SRC-002-source-receipt.json. The planned Latin Modern font dependency is separately subject to its GUST Font License/LPPL terms; no new font embedding is claimed. The preserved SRC-013 font notice is not a license for the rest of this paper.

SRC-003 and SRC-004 have original editable Beamer sources with full original-slide and variant accounting. Historical prose, artwork, style, plotted coordinates, binaries and private navigation are excluded. No source reuse license is invented. Their older ReportLab PDFs remain unchanged and do not render the new sources. Beamer, its transitive packages and Latin Modern need an installed dependency/notice review before any separate native compile; no new font embedding has occurred. See SRC-003-004-disposition.json and SRC-003-004-source-receipt.json.
""")
