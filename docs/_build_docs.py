"""Generate reproducible stakeholder PDF + PPTX, based on inspected requirements."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE = Path(__file__).resolve().parent
BLUE = colors.HexColor('#12233c')
CYAN = colors.HexColor('#087fa4')
GREY = colors.HexColor('#526176')
LIGHT = colors.HexColor('#ebf3f8')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='DocTitle', parent=styles['Title'], fontSize=22, leading=28, textColor=BLUE, spaceAfter=16))
styles.add(ParagraphStyle(name='Subhead', parent=styles['Heading2'], fontSize=12, leading=16, textColor=CYAN, spaceBefore=11, spaceAfter=7, keepWithNext=True))
styles.add(ParagraphStyle(name='DocBody', parent=styles['BodyText'], fontSize=9, leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name='Note', parent=styles['BodyText'], fontSize=8, leading=12, textColor=GREY, spaceAfter=6))


def para(text, style='DocBody'):
    """Format escaped text for the Sprints technical report."""
    return Paragraph(escape(text).replace('\n','<br/>'), styles[style])


def footer(canvas, doc):
    """Identify and number each page of the Sprints technical report."""
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#dae3ea'))
    canvas.line(42, 38, A4[0]-42, 38)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GREY)
    canvas.drawString(42, 26, 'Sprints Multi-Agent Orchestrator | Technical report')
    canvas.drawRightString(A4[0]-42, 26, f'Page {doc.page}')
    canvas.restoreState()

pdf = SimpleDocTemplate(str(BASE/'technical_report.pdf'), pagesize=A4,
                        rightMargin=46,leftMargin=46,topMargin=48,bottomMargin=58)
story = [para('Sprints Multi-Agent AI Career & Assessment Orchestrator','DocTitle'),
         para('Technical report | Groq, Gemini embeddings, LangGraph, Chroma, Docker | 25 November 2026','Note'),
         para('The live CLI used Groq openai/gpt-oss-120b for chat and Gemini gemini-embedding-001 for curriculum search. It verified Chroma retrieval, Docker grading, a SQLite learner lookup and tier-1 approval using the supplied demo data.','DocBody')]

def section(title, *paragraphs):
    """Append a named section on the Sprints workflows or their evidence."""
    story.append(para(title,'Subhead'))
    for p in paragraphs: story.append(para(p))

section('1. Business need and scope',
        'Scale learner support without relying entirely on advisors: answer curriculum questions, execute and assess Python submissions, inspect learner records and support evidence-based career matches. The client explicitly requires one unified LangGraph TypedDict state graph, per-learner session checkpointing, a secure grader sandbox and human oversight for high-trust placements.',
        'Use Groq for intent routing, curriculum evidence checks, rubric feedback and an independent grading judge. Preserve deterministic control over database records and code-test scores.')
section('2. Evidence and data provenance',
        'Inputs include the client kickoff deck, recorded discovery call, project brief and learner CSV.',
        'Important discrepancy: the actual CSV contains 25 learner rows with columns learner_id, name, bootcamp_track, completed_modules, python_assignment_score, target_salary_egp, preferred_employers, readiness_status. The deck mentions 500 rows. No actual Sprints curriculum documents, verified employer vacancies or starter repo URL were provided.',
        'Synthetic curriculum and fictitious job openings are clearly labeled DEMO_ONLY. They are not a claim about Sprints course policies or hiring-partner positions.')
section('3. Agent architecture',
        'One StateGraph routes: Advisor via Chroma -> sufficiency check -> optional query rewrite -> grounded answer; Assessor via sandboxed PythonREPL -> typed feedback -> independent judge -> bounded refine; Learner Record via Groq ReAct and constrained SQL lookup; Career via deterministic SQL eligibility -> mandatory interrupt for tier-1 approval -> final response.',
        'Messages are represented with LangChain HumanMessage, AIMessage and ToolMessage. InMemorySaver (MemorySaver) attaches state to thread_id learner::<id> within a live process. The shell demonstrates continuity but does not provide persistent memory after restart or access-control enforcement.')
section('4. RAG design',
        'Ingestion reads .md and .txt, chunks to 500 cl100k_base tokens with 50-token overlap, attaches source metadata, embeds with Gemini and writes persistent Chroma records. Retrieval uses the top 3 chunks. Groq checks whether the evidence supports an answer and may reformulate the query once.',
        'The Advisor cites its source and returns Unable to verify for unsupported questions. The narrated run measured 17,372 ms for full retrieval, including the Gemini query embedding. Earlier warm Chroma searches with a precomputed vector took 8.48-9.61 ms. Full retrieval exceeded the 1,000 ms target.')
section('5. Assessor and evaluator-optimizer',
        'Rubrics specify expected Python expressions and pass thresholds. Learner code is passed over stdin to a PythonREPL utility running inside an unprivileged Docker container. Tests produce a deterministic numeric score. Groq emits Pydantic feedback and the code sets the score and pass status from executed test results.',
        'A separate Groq call checks the output against the rubric. The workflow allows up to three feedback attempts and withholds a final grade if execution, feedback, or review cannot be verified.',
        'This is an assessment prototype: published tests are susceptible to gaming, and the untrusted execution environment needs production-grade isolation beyond Docker flags.')
section('6. Career matching and escalation',
        'Only observed learner attributes are used: track, completed modules, Python assignment score, target salary, preferred employers and readiness status. Opening requirements must be stored in SQL rather than inferred by the LLM. A candidate is eligible only when all recorded criteria pass.',
        'A tier-1 match enters LangGraph interrupt with a structured reviewer payload. The local shell resumes via Command(resume={approved, reviewer_id}); it demonstrates the interaction contract, not authenticated staff approval. Fictitious demo opening IDs can produce only DEMO MATCH results, never real hiring claims.')
section('7. Threat model, quality bar and failure behavior',
        'Student code execution must fail closed without Docker. Runtime controls include a network-denied, read-only Docker container with no privileges/caps, low-resource budgets, non-root UID and bounded execution time. For production, use a dedicated sandbox platform such as a microVM or gVisor and add hard output quotas, forced container cleanup, hidden tests and threat assessment.',
        'SQL queries are parameterized and read-only, not arbitrary model-generated statements. Prompt injection in documents remains a risk; retrieved text is treated as evidence, never as authority to run tools.',
        'Twelve offline tests passed on Windows. The live session produced a 100/100 grade from 3/3 Docker tests. The same learner thread displayed retrieval timing for the Advisor turn and cleared it before grading. Deployment p95 and business impact still need measurement.')
section('8. Tradeoffs and rollout',
        'Routing, evidence checks and rubric review use separate Groq calls. The memory saver provides continuity during a local process. Curriculum search depends on a network call to Gemini for each query embedding.',
        'Pilot milestones include indexing official course material, connecting verified openings, authenticating learners and staff, persisting checkpoints, hardening the grader, and benchmarking fresh curriculum queries.')
section('9. Deliverable status',
        'The submission includes a narrated Groq CLI walkthrough, source code, tests, SQLite data, notebook, charter and stakeholder slides. The recorded Fawry match uses a fictional opening and a simulated staff review.')
story.append(Spacer(1,10))
story.append(para('Reference guides include LangChain Groq and Gemini integrations, LangGraph interrupts, Chroma integration and Docker security guidance.','Note'))
pdf.build(story, onFirstPage=footer, onLaterPages=footer)

slides = [
 ('Sprints AI Career & Assessment Orchestrator', 'Groq chat and Gemini curriculum embeddings',
  ['Stakeholder demo architecture | Sprints Advanced Agentic AI', 'Based on the client kickoff and discovery call', 'Demonstration build, not a production release']),
 ('Why this matters', 'Manual work becomes the bottleneck',
  ['Curriculum questions overwhelm student-success advisors', 'Manual Python marking slows technical feedback', 'Matching graduates to partners requires verifiable evidence', 'Target: reduce response time and eliminate unsupported placements']),
 ('System: one unified LangGraph StateGraph', 'Typed state, worker routing, checkpoints',
  ['The Groq router selects one of four worker paths', 'Student-specific thread_id and MemorySaver session state', 'HumanMessage / AIMessage / ToolMessage traces', 'Human-in-the-loop gate before tier-1 placements']),
 ('Advisor: grounded curriculum answers', 'Agentic RAG with self-reflection',
  ['500-token chunks | 50-token overlap | ChromaDB', 'Gemini embeddings -> retrieve top-3 excerpts', 'Judge context sufficiency; rewrite at most once', 'Cite source filenames; fail closed when not supported']),
 ('Assessor: secure Python grading', 'Docker test results and Groq feedback',
  ['PythonREPL runs inside restricted Docker, not host', 'Typed JSON: score / feedback_points / pass_status', 'Deterministic tests determine score and pass status', 'A separate Groq call reviews up to three feedback attempts']),
 ('Career matching without hallucination', 'Deterministic SQL filters + HITL',
  ['Use recorded track, modules, grade, salary and preferences only', 'No employer job requirements inferred from thin learner data', 'Tier-1 opening -> interrupt -> explicit human decision', 'DEMO jobs remain visibly fictional even after review']),
 ('Live demo results', 'Groq, Chroma, Docker and LangGraph',
  ['Advisor cited the synthetic curriculum source', 'Docker graded the Python submission 100/100 on 3 tests', 'SQLite checked learner and opening criteria', 'LangGraph paused for reviewer approval before showing the fictional Fawry match']),
 ('Security, constraints and measurable KPIs', 'Measured on the supplied demo fixtures',
  ['Without Docker, grading returns Unable to verify', 'Retrieval took 17.37 s against a 1 s target', 'Learner wait-time reduction still needs measurement', 'Production needs authenticated approvals and durable checkpoints']),
 ('Pilot readiness', 'What the live demo establishes',
  ['25 learner records imported. All 12 offline tests passed', 'Official curriculum and real openings are needed for a pilot', 'The narrated walkthrough shows the Groq CLI results', 'Pilot needs staff authentication and retrieval benchmarking']),
]

prs=Presentation()
prs.slide_width=Inches(13.333)
prs.slide_height=Inches(7.5)

def ppt_text(slide, x,y,w,h, text, size=20,bold=False,color=(18,35,60),align=PP_ALIGN.LEFT):
    """Place editable text on a Sprints stakeholder slide."""
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=box.text_frame
    tf.clear(); tf.word_wrap=True
    for i, line in enumerate(text.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=line; p.alignment=align
        p.font.size=Pt(size); p.font.bold=bold; p.font.color.rgb=RGBColor(*color)
        p.space_after=Pt(8)
    return box

for ix,(title,subtitle,bullets) in enumerate(slides,1):
    s=prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor(246,250,253)
    bar=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,prs.slide_width,Inches(0.12))
    bar.fill.solid();bar.fill.fore_color.rgb=RGBColor(8,127,164);bar.line.fill.background()
    ppt_text(s,0.8,0.7,11.7,0.8,title,33,True)
    ppt_text(s,0.83,1.57,11.7,0.45,subtitle,19,False,(8,127,164))
    if ix==1:
        ppt_text(s,0.83,2.78,11.4,2.5,'\n'.join(bullets),22,False)
    else:
        for j,b in enumerate(bullets):
            x=0.8+(j%2)*6.1;y=2.35+(j//2)*1.8
            panel=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(5.7),Inches(1.55))
            panel.fill.solid();panel.fill.fore_color.rgb=RGBColor(232,242,248);panel.line.color.rgb=RGBColor(213,227,237)
            ppt_text(s,x+0.25,y+0.25,5.2,1.1,b,19,False)
    ppt_text(s,0.8,7.0,10,0.25,'Sprints demo architecture',10,False,(82,97,118))
    ppt_text(s,11.8,7.0,0.7,0.25,f'{ix:02}',10,False,(82,97,118),PP_ALIGN.RIGHT)
prs.save(BASE/'final_presentation.pptx')

# Slide PDF uses the same slide content without depending on LibreOffice.
from reportlab.pdfgen import canvas
slidepdf = canvas.Canvas(str(BASE/'final_presentation.pdf'),pagesize=landscape((960,540)))
for ix,(title,subtitle,bullets) in enumerate(slides,1):
    slidepdf.setFillColor(colors.HexColor('#f6fafd'));slidepdf.rect(0,0,960,540,fill=1,stroke=0)
    slidepdf.setFillColor(CYAN);slidepdf.rect(0,532,960,8,fill=1,stroke=0)
    slidepdf.setFillColor(BLUE);slidepdf.setFont('Helvetica-Bold',28)
    slidepdf.drawString(52,472,title)
    slidepdf.setFillColor(CYAN);slidepdf.setFont('Helvetica',17)
    slidepdf.drawString(52,435,subtitle)
    for j,item in enumerate(bullets):
        x, y = (52, 310 - j * 46) if ix == 1 else (52 + (j % 2) * 448, 315 - (j // 2) * 135)
        if ix!=1:
            slidepdf.setFillColor(LIGHT);slidepdf.roundRect(x,y,420,108,12,fill=1,stroke=0)
        slidepdf.setFillColor(BLUE);slidepdf.setFont('Helvetica',16 if ix == 1 else 13)
        # simple line wrap bounded to card width
        import textwrap
        wrap=textwrap.wrap(item, width=80 if ix == 1 else 49)
        for lno,line in enumerate(wrap): slidepdf.drawString(x+14,y+76-19*lno,line)
    slidepdf.setFillColor(GREY);slidepdf.setFont('Helvetica',9)
    slidepdf.drawString(52,24,'Sprints demo architecture')
    slidepdf.drawRightString(909,24,f'{ix:02d}')
    slidepdf.showPage()
slidepdf.save()
print('Generated',len(slides),'slides and technical report')
