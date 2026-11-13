from pathlib import Path
import html
from reportlab import rl_config
rl_config.invariant = 1
P=Path(__file__).resolve().parent; P.mkdir(exist_ok=True)
sections=[
('A bounded system for authorized work', '''Runspindle is a proposed distribution of cooperating components for agent-assisted work. Its aim is to make task boundaries, human control, evidence, and recovery explicit. The current deliverable is a scaffold and design specification. It is not an operating service, a production deployment, or a measured improvement over a native agent product.
A task begins with a defined outcome, accountable owner, permitted sources and actions, and stop conditions. An agent's ability to perform an action is not authority to perform it. Scope changes and consequential actions require the applicable approval. Product policy and legal constraints remain in force; the architecture is not a mechanism for bypassing them.'''),
('Why a specialist harness might help', '''A general-purpose agent can leave work unfinished even when a bounded, permitted path exists. The useful engineering question is whether a narrow integration can improve verified completion without expanding authority. Additional prompting, retries, and tool calls can also increase cost or create duplicate external effects. Runspindle therefore treats completion, authorization, and recovery as separate things to verify.
A future comparison should hold the task and permission boundary constant. Native assistance, expert-guided assistance, and the proposed harness should receive matched tasks. Count failures, human intervention, and uncertain results, rather than reporting only successful examples. No such comparative Runspindle study has been completed.'''),
('Seven components with separate responsibilities', '''Core is planned in Rust with Temporal for durable task state, approval waits, and explicit retry and reconciliation decisions. Host is the proposed native Codex integration and owns host/session identity checks. Browser is planned around OpenBao secret references, PinchTab actions, and a KasmVNC human view of the same browser.
Tether is intended to adapt the existing Tether Slack integration, with verified actors and bounded routing rather than granting authority from message arrival. Refinery is the proposed Python DSPy experiment layer. Console is intended to show actual fleet observations, including their age and unknown states; the current scaffold has no connected fleet. Platform owns the proposed distribution manifests, release packaging, development environment, and deployment gates.
These are component contracts, not assertions that their integrations work. Naming a technology does not establish compatibility, availability, or a security guarantee.'''),
('Browser control and human takeover', '''The intended browser model is one isolated account context, one headed browser, and one current controller. A broker would bind commands to account, task, actor, and lease epoch. PinchTab would provide the action interface. KasmVNC passive viewing is proposed as a separate, authorized read-only mode that grants no input control. Interactive takeover would require a fresh fenced control lease on the same browser. A handoff must invalidate old commands and revoke existing input and streams before granting a new epoch.
OpenBao is proposed for secret references and controlled credential access. Credentials and browser profiles must not enter logs, public artifacts, or model evaluation datasets. Temporal records durable intent; it cannot by itself fence browser input or prove whether a website accepted a submission. After an ambiguous external action, the workflow must reconcile observable state before retrying. These properties still require Runspindle integration and adversarial tests.'''),
('Refinement without default collection', '''The proposed refinery begins only with an explicitly selected workflow and authorized examples. Review and redaction precede dataset entry. Dataset versions should retain source permission, adjudication, group identifiers, and stable train, validation, and held-out splits. Related examples must remain in the same split to reduce leakage. Proposed feedback records would bind attributable reactions or replies to the exact output and its version. Task-specific automatic gold rules may admit examples only under explicit criteria; conflicting signals must be quarantined for adjudication. Gold eligibility is separate from candidate release approval.
Python DSPy candidates would be compared with a baseline under a fixed task definition and evaluation budget. Quality, safety failures, latency, human repair, and total cost belong in the comparison. Experiments cannot promote themselves. A versioned release needs threshold evidence, human authorization, and a rollback reference. No live collection, provider invocation, training, promotion, or saving is claimed.'''),
('Economics of accepted work', '''Cost per accepted authorized task is total model, tool, human, verification, maintenance, and recovery cost divided by the number of verified authorized completions. Include failed attempts and cleanup in the numerator. If there are no accepted completions, report the cost and zero completions rather than a misleading unit price.
A specialist system also has fixed integration and evaluation costs. Low-volume workflows may remain cheaper with manual assistance. Break-even depends on measured workload mix, acceptance rate, maintenance cadence, and labor assumptions. Saved minutes do not automatically become cash savings. Provider improvements may remove the advantage of a custom harness, so repeat comparisons after material model or platform changes. Runspindle has no measured savings, prices, break-even point, or market-size estimate.'''),
('Fleet evidence and uncertainty', '''A fleet view should distinguish a planned component, an observed process, a managed session, and a verified terminal result. Every observation needs a timestamp, source, and freshness policy. Missing updates mean unknown state, not automatic proof of failure. Control actions need a verified binding to the intended host, repository, process, and session.
Console should eventually render those actual observations rather than synthetic success indicators. Tether messages may link to a bounded task or evidence record, but message delivery is not execution completion. A stale route, recycled process identifier, or disconnected host must not silently redirect an action. Standard Collectors and Langfuse integration are proposed for correlated task, session, trace, and output identity with readback verification. Masking coverage remains unresolved across those paths; no complete redaction guarantee is claimed. The scaffold does not yet collect or render live observations.'''),
('Evaluation and release gates', '''Development validation should test contracts and synthetic fixtures first: lease fencing, isolation, duplicate requests, restart recovery, permission changes, cancellation, stream revocation, and unknown external outcomes. Integration tests then need pinned component versions and permissioned environments. No source repository's historical test result transfers automatically to the new system.
Production readiness requires independently evidenced secrets management, authenticated routing, monitoring, rollback, dependency review, and operator acceptance. Packaging a manifest is not deployment; a passing stub test is not proof of a live system. Development and production deployment remain planned. The distribution must fail closed when prerequisites or authorization are missing.'''),
('Claims, sources, and open questions', '''This migration adapts selected concepts under opaque source identifiers SRC-002, SRC-013, and SRC-009. These are partial migrations and newly written adaptations, not faithful re-renders. Historical PDFs are preserved separately and are not Runspindle builds. Detailed source provenance and review records are kept outside the public candidate. Source selection does not establish a new project license or third-party endorsement.
The next useful evidence is a reproducible, permissioned end-to-end task that traverses the component boundaries and demonstrates recovery from an uncertain result. Until then, the materials describe a research and engineering plan. Open questions include native session integration, browser lifecycle compatibility, least-privilege secret delivery, evaluation validity, release reproducibility, and operational cost.''')]
pre=r'''\documentclass[11pt]{article}
\usepackage[margin=0.95in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern,microtype,hyperref,enumitem}
\hypersetup{colorlinks=true,urlcolor=blue,linkcolor=blue}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.65em}
'''
def tex(s): return s.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_')
def article(name,title,parts):
 body=pre+'\\title{'+title+'}\\author{Runspindle}\\date{Design scaffold | November 2026}\n\\begin{document}\\maketitle\n\\textbf{Status: planned architecture. No live implementation, deployment, benchmark, or savings claim.}\n'
 for h,t in parts: body+='\\section{'+tex(h)+'}\n'+tex(t)+'\n'
 body+='\\end{document}\n'; (P/(name+'.tex')).write_text(body)
article('runspindle-paper','Runspindle: Authorized Work as a Verifiable System',sections)
article('workflow-refinery','Runspindle Refinery: A Human-Guided Evaluation Loop',[sections[i] for i in [0,4,5,7,8]])
(P/'economics.md').write_text('# Runspindle economics\n\nStatus: proposed accounting model; no measured results.\n\n'+sections[5][1]+'\n\nSource concept: SRC-005.\n')
(P/'overview.md').write_text('# Runspindle\n\n'+'\n\n'.join('## '+h+'\n\n'+t for h,t in sections)+'\n')
style='body{max-width:72rem;margin:auto;padding:3rem 1.5rem;font:18px/1.65 system-ui;color:#183247;background:#f7fafc}h1{font-size:3rem;line-height:1.1}h2{line-height:1.25;margin-top:2.6rem}p{max-width:78ch}.badge{color:#6b3600;background:#fff0d3;padding:1rem;border-radius:.6rem}a{color:#075985}nav{display:flex;gap:1rem;flex-wrap:wrap}footer{border-top:1px solid #b8c8d2;margin-top:3rem;padding-top:1rem}'
def page(name,title,parts):
 b='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+title+'</title><style>'+style+'</style><body><nav><a href="index.html">Overview</a><a href="browser.html">Browser</a><a href="vision.html">Refinery</a></nav><main><h1>'+title+'</h1><p class="badge">Design scaffold. Integrations and deployments are planned. No measured savings or live fleet is claimed.</p>'
 for h,t in parts: b+='<section><h2>'+html.escape(h)+'</h2>'+''.join('<p>'+html.escape(x)+'</p>' for x in t.split('\n'))+'</section>'
 b+='</main><footer>Runspindle design materials. Source concepts: SRC-002, SRC-013, SRC-009. Historical artifacts are not new builds. Third-party products retain their own names and licenses.</footer></body></html>'
 (P/name).write_text(b)
page('index.html','Runspindle',[sections[i] for i in [0,2,6,7,8]])
page('browser.html','Runspindle Browser',[sections[i] for i in [0,3,6,7]])
page('vision.html','Runspindle Refinery',[sections[i] for i in [4,5,7,8]])
def deck(name,title,parts):
 b=r'''\documentclass[aspectratio=169,11pt]{beamer}
\usepackage[T1]{fontenc}\usepackage{lmodern}
\setbeamertemplate{navigation symbols}{}
\setbeamertemplate{footline}[frame number]
\setbeamercolor{structure}{fg=blue!55!black}
'''+ '\\title{'+title+'}\\subtitle{Design scaffold; no live deployment or measured savings}\\author{Runspindle}\\date{November 2026}\\begin{document}\\begin{frame}\\titlepage\\end{frame}\n'
 for h,bullets in parts:
  b+='\\begin{frame}{'+tex(h)+'}\\begin{itemize}\n'+''.join('\\item '+tex(x)+'\n' for x in bullets)+'\\end{itemize}\\end{frame}\n'
 b+='\\end{document}\n';(P/(name+'.tex')).write_text(b)
deck('argument','Runspindle: The Case for Verified Work',[
('The problem',['A tool call is not an accepted outcome.','Human repair, retries, and uncertain external effects belong in the cost.','A harness must preserve task authority rather than expand it.']),
('The proposed system',['Core: Rust and Temporal. Host: native Codex.','Browser: OpenBao, PinchTab, KasmVNC. Tether: existing Slack integration.','Refinery: Python DSPy. Console: actual fleet views. Platform: distribution.','All new integrations remain scaffolded.']),
('A measurable claim',['Compare native, expert-guided, and harness-assisted work on matched tasks.','Predeclare acceptance, authorization, failure, and stop rules.','Count every attempt and human intervention. No results are asserted.']),
('Refinement with gates',['Select and authorize; review and redact; curate grouped held-out data.','Compare candidates on quality, safety, latency, and full cost.','Bind attributable reactions/replies to exact outputs; task-specific gold rules quarantine conflicts.','Gold eligibility is separate from human-approved candidate release and rollback.']),
('Economics without a forecast',['Divide total operating cost by verified authorized completions.','Include setup, maintenance, verification, recovery, and failed attempts.','Low volume or provider improvements can erase a proposed advantage.']),
('Next evidence',['Demonstrate a permissioned end-to-end task and uncertain-result recovery.','Verify component contracts before any production claim.','Historical source evidence is separate from Runspindle results. Source: SRC-002, SRC-013.'])])
deck('fleet','Runspindle: Fleet Evidence and Control',[
('State must be observable',['A process observation is not a managed session or a completed task.','Every record needs identity, timestamp, source, and freshness.','Missing updates mean unknown, not permission to restart.']),
('Bind control to identity',['Verify host, repository, process, session, and task before an action.','Native Codex is the planned host boundary.','Tether routes bounded requests; delivery alone proves no outcome.']),
('One browser, one controller',['Authorized passive KasmVNC viewing grants no input control.','Interactive takeover needs a fenced lease on the same browser as PinchTab.','Fence stale lease epochs and revoke streams on handoff.','OpenBao secret references must stay out of logs and evaluation data.']),
('Durability is not external certainty',['Temporal stores durable intent and approval waits.','An uncertain submission requires reconciliation before retry.','Browser-side fencing and account isolation need separate tests.']),
('Console and release evidence',['Planned console views must use actual fleet observations with age.','Collectors/Langfuse identity and readback are proposed; masking coverage remains unresolved.','No live fleet is connected in this scaffold.','Platform packaging, development integration, and production acceptance remain planned.']),
('A bounded validation plan',['Test stale routes, recycled process IDs, cancellation, restart, and duplicate requests.','Use permissioned environments; do not inherit historical success claims.','No implementation, deployment, or savings result is claimed. Source: SRC-002, SRC-009.'])])
(P/'THIRD_PARTY_NOTICES.md').write_text('''# Third-party notices and source status

Runspindle names Rust, Temporal, Codex, OpenBao, PinchTab, KasmVNC, Slack, Python, DSPy, and Langfuse only to identify proposed integrations. No endorsement is implied, and this document does not relicense those products.

SRC-013 selected source material carries the MIT notice: Copyright (c) 2026 newdarwindev. The complete original notice is retained in LICENSE-SRC-013.txt. The permission notice applies to that source material and its adapted portions, not automatically to this entire distribution.

No project license was found for SRC-002 or SRC-009 during source review. No license is invented or assigned to them here. Detailed provenance and original artifacts remain in restricted migration records outside this public candidate. A publisher must resolve the rights to any retained expression before release.

The public candidate contains newly written narrative and diagrams-free documents; it does not republish historical PDFs, original third-party figures, bibliography entries, or private operational evidence. The historical source bibliography is preserved unmodified in the separate source archive, not represented as fresh verification of external claims.
''')

from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
import re
S=getSampleStyleSheet();S.add(ParagraphStyle(name='Copy',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=10,textColor=colors.HexColor('#183247')))
S['Heading1'].textColor=colors.HexColor('#075985');S['Title'].textColor=colors.HexColor('#183247')
def foot(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#566877'));c.drawString(50,28,'RUNSPINDLE / DESIGN SCAFFOLD / NEW DOCUMENT');c.drawRightString(d.pagesize[0]-50,28,str(d.page))
def paper(name,title,parts):
 story=[Paragraph(title,S['Title']),Paragraph('November 2026 | Design scaffold',S['Heading2']),Paragraph('No live implementation, deployment, benchmark, or savings claim.',S['Copy'])]
 for h,t in parts:
  story.append(Paragraph(h,S['Heading1']))
  for para in t.split('\n'):story.append(Paragraph(html.escape(para),S['Copy']))
 SimpleDocTemplate(str(P/(name+'.pdf')),rightMargin=52,leftMargin=52,topMargin=42,bottomMargin=48,title=title,author='Runspindle').build(story,onFirstPage=foot,onLaterPages=foot)
paper('runspindle-paper','Runspindle: Authorized Work as a Verifiable System',sections)
paper('workflow-refinery','Runspindle Refinery: A Human-Guided Evaluation Loop',[sections[i] for i in [0,4,5,7,8]])
for name in ['argument','fleet']:
 source=(P/(name+'.tex')).read_text();title=re.search(r'\\title\{([^}]+)',source)[1]
 story=[Paragraph(title,S['Title']),Spacer(1,24),Paragraph('Design scaffold; no live deployment or measured savings.',S['Heading2']),Paragraph('November 2026',S['Copy']),PageBreak()]
 for h,body in re.findall(r'\\begin\{frame\}\{([^}]+)\}(.*?)\\end\{frame\}',source,re.S):
  story.append(Paragraph(h,S['Title']));story.append(Spacer(1,18))
  for bullet in re.findall(r'\\item (.*)',body):story.append(Paragraph(html.escape(bullet),ParagraphStyle(name='slide',parent=S['Copy'],fontSize=17,leading=24,spaceAfter=18,bulletIndent=0,leftIndent=16),bulletText='-'))
  story.append(PageBreak())
 story.pop()
 SimpleDocTemplate(str(P/(name+'.pdf')),pagesize=(960,540),rightMargin=60,leftMargin=60,topMargin=55,bottomMargin=52,title=title,author='Runspindle').build(story,onFirstPage=foot,onLaterPages=foot)
