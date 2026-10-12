"""Combined research working report. Refuses to publish fewer than 50 tasks.

No evaluated code, hooks, graders, credentials or model calls execute here.
"""
import csv,json,math
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tmp/pdf-report-deps'))
from xml.sax.saxutils import escape
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,Color,white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
from scripts.analyze50 import analyze,OUT,ROOT,NEM,SHARED,TASKS,LANGS,MODELS,read,sha
from bench.durable import atomic_json
from bench.lease import ControllerLease

DEST=ROOT/'output/pdf';FIG=DEST/'figures';PDF=DEST/'Indic_Harness_Bench_50_Task_Combined_Report.pdf'
NAVY='#16334a';BLUE='#246b9e';TEAL='#16806c';ORANGE='#c56c35';GRAY='#63768a'
names={'oss':'GPT-OSS-20B','nemotron':'Nemotron 3 Super'};langnames={'en':'English','hi':'Hindi','hinglish':'Hinglish'}
cats={'Workspace, Tool Use & Multimodal Operations':'Workspace / tools','Office & Business Communication':'Office / writing','Knowledge, Evidence & Retrieval':'Knowledge / evidence','Software Engineering & Codebase Maintenance':'Software / code','Data, BI & Finance Analytics':'Data / finance','Long-running Autonomy & State Adaptation':'State / autonomy','SRE, DevOps & Release Ops':'SRE / release','Vertical Professional Workflows':'Professional workflows'}

def savefig(name,fig):
    FIG.mkdir(parents=True,exist_ok=True)
    fig.savefig(FIG/(name+'.png'),dpi=190,bbox_inches='tight',facecolor='white');fig.savefig(FIG/(name+'.svg'),bbox_inches='tight',facecolor='white');plt.close(fig)
def short(c):return cats.get(c,c.replace(' & ',' / '))
def charts(s,rows,atlas):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#b5c2cc','axes.labelcolor':NAVY,'xtick.color':GRAY,'ytick.color':GRAY,'axes.titlecolor':NAVY,'grid.color':'#e4ebf0','svg.fonttype':'none'})
    x=np.arange(3);w=.34
    fig,ax=plt.subplots(figsize=(7.1,3.6))
    for i,m in enumerate(MODELS):
        vals=[s['models'][m][l]['mean_score'] for l in LANGS];bars=ax.bar(x+(i-.5)*w,vals,w,label=names[m],color=[BLUE,TEAL][i])
        ax.bar_label(bars,fmt='%.1f',padding=4,fontsize=10)
    ax.set_xticks(x,[langnames[l] for l in LANGS]);ax.set_ylim(0,108);ax.set_ylabel('Mean original oracle score / 100');ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(0,1.15));ax.yaxis.grid(True);ax.set_axisbelow(True);savefig('01_mean_scores',fig)
    fig,ax=plt.subplots(figsize=(7.1,3.2))
    for i,m in enumerate(MODELS):
        vals=[100*s['models'][m][l]['full_count']/50 for l in LANGS];b=ax.bar(x+(i-.5)*w,vals,w,label=names[m],color=[BLUE,TEAL][i]);ax.bar_label(b,labels=[f"{s['models'][m][l]['full_count']}/50" for l in LANGS],padding=4)
    ax.set_xticks(x,[langnames[l] for l in LANGS]);ax.set_ylim(0,max(30,max(vals)+10));ax.set_ylabel('Strict full completions (%)');ax.yaxis.grid(True);ax.set_axisbelow(True);ax.legend(frameon=False);savefig('02_full_completion',fig)
    keys=['model_en','model_hi','model_hinglish','model_overall'];fig,ax=plt.subplots(figsize=(7.1,3.6))
    for i,k in enumerate(keys):
        r=s['contrasts'][k];v=r['mean_difference_pp'];lo,hi=r['ci'];ax.errorbar(v,3-i,xerr=[[v-lo],[hi-v]],fmt='o',color=TEAL,capsize=4,markersize=7)
        ax.text(hi+1,3-i,f'{v:+.1f} [{lo:+.1f}, {hi:+.1f}]',va='center',fontsize=9)
    ax.set_yticks(range(4),['Task average','Hinglish','Hindi','English']);ax.axvline(0,color=GRAY,linestyle='--');ax.set_xlabel('Nemotron minus GPT-OSS score (percentage points)');lim=[min(s['contrasts'][k]['ci'][0] for k in keys)-5,max(s['contrasts'][k]['ci'][1] for k in keys)+22];ax.set_xlim(lim);ax.set_ylim(-.5,3.5);ax.xaxis.grid(True);savefig('03_model_contrasts',fig)
    fig,axs=plt.subplots(1,3,figsize=(7.1,2.9),sharex=True,sharey=True)
    for ax,l in zip(axs,LANGS):
        a=[r['oss_'+l] for r in atlas];b=[r['nemotron_'+l] for r in atlas];ax.scatter(a,b,c=[ORANGE if r['added'] else TEAL for r in atlas],s=27,alpha=.8,edgecolor='white',linewidth=.3);ax.plot([0,100],[0,100],color=GRAY,lw=.8);ax.set_title(langnames[l]);ax.set_xlim(-4,104);ax.set_ylim(-4,104);ax.set_xlabel('GPT-OSS score');ax.set_aspect('equal')
    axs[0].set_ylabel('Nemotron score');fig.tight_layout();savefig('04_paired_scores',fig)
    fig,ax=plt.subplots(figsize=(7.1,3.5));keys=['oss_en_minus_hi','oss_en_minus_hinglish','nemotron_en_minus_hi','nemotron_en_minus_hinglish'];labels=['GPT-OSS: EN - HI','GPT-OSS: EN - HG','Nemotron: EN - HI','Nemotron: EN - HG']
    for i,k in enumerate(keys):
        r=s['contrasts'][k];v=r['mean_difference_pp'];lo,hi=r['ci'];ax.errorbar(v,3-i,xerr=[[v-lo],[hi-v]],fmt='o',color=BLUE if i<2 else TEAL,capsize=4);ax.text(hi+1,3-i,f'{v:+.1f} [{lo:+.1f}, {hi:+.1f}]',fontsize=9,va='center')
    ax.set_yticks([3,2,1,0],labels);ax.axvline(0,color=GRAY,linestyle='--');ax.set_xlabel('English minus other-language score (percentage points)');ax.set_xlim(min(s['contrasts'][k]['ci'][0] for k in keys)-4,max(s['contrasts'][k]['ci'][1] for k in keys)+22);ax.set_ylim(-.5,3.5);savefig('05_language_contrasts',fig)
    fig,ax=plt.subplots(figsize=(7.1,4.0));cs=sorted(s['categories'],key=lambda c:c['difference_pp'])
    for i,c in enumerate(cs):
        a=c['means']['oss'];b=c['means']['nemotron'];ax.plot([a,b],[i,i],color='#aabac5',lw=2);ax.scatter([a],[i],color=BLUE,s=46,label=names['oss'] if i==0 else None);ax.scatter([b],[i],color=TEAL,s=46,label=names['nemotron'] if i==0 else None)
    ax.set_yticks(range(len(cs)),[short(c['category'])+f" (n={c['tasks']})" for c in cs]);ax.set_xlim(0,105);ax.set_xlabel('Mean score / 100, averaged over three languages');ax.legend(frameon=False,loc='lower right');ax.xaxis.grid(True);savefig('06_categories',fig)
    fig,axs=plt.subplots(1,3,figsize=(7.1,3.0))
    for ax,field,title,divisor in zip(axs,['elapsed_sec','known_input_tokens','known_output_tokens'],['Elapsed minutes','Known input (thousands)','Known output (thousands)'],[60,1000,1000]):
        vals=[[r[field]/divisor for r in rows if r['model']==m and r[field] is not None] for m in MODELS]
        bp=ax.boxplot(vals,tick_labels=['OSS','Nemotron'],showfliers=False,patch_artist=True,widths=.48)
        for p,color in zip(bp['boxes'],[BLUE,TEAL]):p.set_facecolor(color);p.set_alpha(.7)
        ax.set_title(title,fontsize=10);ax.yaxis.grid(True);ax.set_axisbelow(True)
    fig.tight_layout();savefig('07_resources',fig)
    fig,axs=plt.subplots(2,1,figsize=(7.1,9.0),gridspec_kw={'height_ratios':[25,25]})
    labels=['OSS EN','OSS HI','OSS HG','Nem EN','Nem HI','Nem HG']
    for ax,part in zip(axs,[atlas[:25],atlas[25:]]):
        z=np.array([[r[m+'_'+l] for m in MODELS for l in LANGS] for r in part]);im=ax.imshow(z,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto')
        ax.set_xticks(range(6),labels);ax.set_yticks(range(len(part)),[r['task_id'].split('-',1)[0]+' '+r['task_id'].split('-',1)[1][:27]+(' *' if r['added'] else '') for r in part],fontsize=8)
        for i in range(len(part)):
            for j in range(6):ax.text(j,i,f'{z[i,j]:.0f}',ha='center',va='center',fontsize=7,color='white' if z[i,j]>60 else NAVY)
        ax.tick_params(length=0)
    fig.tight_layout();savefig('08_task_heatmap',fig)

def fonts():
    for name,file in [('Body','segoeui.ttf'),('Bold','segoeuib.ttf'),('Italic','segoeuii.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')

def report(s,rows,atlas):
    fonts();story=[];CW=A4[0]-94
    styles={
      'body':ParagraphStyle('body',fontName='Body',fontSize=9.5,leading=14,textColor=HexColor(NAVY),spaceAfter=9),
      'title':ParagraphStyle('title',fontName='Bold',fontSize=31,leading=36,textColor=HexColor(NAVY),spaceAfter=18),
      'h1':ParagraphStyle('h1',fontName='Bold',fontSize=21,leading=26,textColor=HexColor(NAVY),spaceAfter=13),
      'h2':ParagraphStyle('h2',fontName='Bold',fontSize=12,leading=17,textColor=HexColor(TEAL),spaceBefore=8,spaceAfter=7),
      'small':ParagraphStyle('small',fontName='Body',fontSize=8,leading=11,textColor=HexColor(GRAY),spaceAfter=8),
      'cell':ParagraphStyle('cell',fontName='Body',fontSize=8.2,leading=11,textColor=HexColor(NAVY)),
      'headcell':ParagraphStyle('headcell',fontName='Bold',fontSize=8.2,leading=11,textColor=white),
      'kicker':ParagraphStyle('kicker',fontName='Bold',fontSize=10,leading=14,textColor=HexColor(TEAL),spaceAfter=17)}
    def p(text,kind='body'):story.append(Paragraph(text,styles[kind]))
    def page(title):story.append(PageBreak());p(title,'h1')
    def table(data,widths=None,padding=7,space_after=11):
        cooked=[[Paragraph(str(x),styles['headcell' if i==0 else 'cell']) for x in row] for i,row in enumerate(data)]
        t=Table(cooked,colWidths=widths or [CW/len(data[0])]*len(data[0]),repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(NAVY)),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor('#f0f5f8')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding),('LINEBELOW',(0,0),(-1,0),.5,white)]));story.append(t)
        if space_after:story.append(Spacer(1,space_after))
    def fig(name,height,caption):
        from PIL import Image as PI
        w,h=PI.open(FIG/(name+'.png')).size;scale=min(CW/w,height/h);story.append(Image(str(FIG/(name+'.png')),width=w*scale,height=h*scale,hAlign='CENTER'));p(caption,'small')
    def val(m,l,k='mean_score'):return s['models'][m][l][k]
    def ci(r):return f"{r['mean_difference_pp']:+.2f} [{r['ci'][0]:+.2f}, {r['ci'][1]:+.2f}]"
    overall=s['contrasts']['model_overall'];avgs={m:np.mean([val(m,l) for l in LANGS]) for m in MODELS}
    p('INDIC HARNESS BENCH · RESEARCH WORKING REPORT','kicker')
    p('A matched 50-task<br/>comparison of two<br/>agent models','title')
    p('GPT-OSS-20B and Nemotron 3 Super through OpenClaw','h2')
    p('English, Hindi and Hinglish instructions · 2 October 2026','small')
    story.append(Spacer(1,19))
    table([['Independent task units','Conditions per model','Scored conditions'],['50','150','300']])
    p('Executive findings','h2')
    p(f"Across the same 50 tasks, Nemotron averaged <b>{avgs['nemotron']:.2f}/100</b> and GPT-OSS averaged <b>{avgs['oss']:.2f}/100</b>. The paired model difference, averaged over the three languages within each task, was <b>{overall['mean_difference_pp']:+.2f} percentage points</b> (95% task bootstrap interval {overall['ci'][0]:+.2f} to {overall['ci'][1]:+.2f}). Task-level results varied widely; these averages describe this model-harness configuration and selected task set.")
    p('This report combines the retained 46-task comparison with four newly evaluated tasks under the same logical study. Only 24 new primary conditions were run. Every previous result and the earlier GPT-OSS PDF remain intact. Infrastructure recoveries are shown in the evidence history; ordinary low scores and budget-exhausted outcomes remain in the analysis.')
    p('Hindi has the highest mean score for both models. English exceeds Hinglish on average, but all four within-model language intervals include zero. This dataset therefore does not establish a consistent language-degradation effect. Strict full completions remain uncommon: 13/150 for GPT-OSS and 18/150 for Nemotron. A completed process often produced only a partial task solution.')
    p('Prepared for the team’s mid-semester report and subsequent paper planning. This is an exploratory research record, not a submission-ready paper. AI-assisted translations and analysis require team review before publication.','small')

    page('1. Study population and design')
    p('The experiment changes the instruction language while holding each task’s local fixtures, expected output paths, schemas, English prose deliverables and deterministic grader fixed. Each original task supplies six matched conditions: two models × three languages. The independent sampling unit is the original task, not its six condition records.')
    table([['Population step','Tasks','Language conditions'],['Original GPT-OSS campaign','54','162 primary'],['Retained after whole-task primary INFRA exclusion','46','138 per model'],['Previously unused additions, evaluated on both models','4','12 per model'],['Combined matched study','50','150 per model / 300 total']], [CW*.64,CW*.12,CW*.24])
    p('Why 50 samples is now a defensible description','h2')
    p('There are 50 distinct task units, with three language versions evaluated on each model. There are also 300 scored condition records. The report uses <b>n = 50 tasks</b> for paired uncertainty and states the larger condition count separately; it does not claim 300 independent samples.')
    p('The original eight excluded GPT-OSS task groups remain excluded. Nemotron used that preselected 46-task scope and later infrastructure recoveries. The four additions were chosen after both previous campaigns had produced outcomes, before any new model outcome was observed. Selection favored unused, offline, single-round tasks in less represented families; it was not random sampling or a preregistered 50-task design.')
    table([['Task family','Distinct tasks']]+[[short(c['category']),c['tasks']] for c in s['categories']],[CW*.8,CW*.2])

    page('2. Execution and grading protocol')
    table([['Setting','GPT-OSS-20B','Nemotron 3 Super'],['Provider model ID','gpt-oss:20b','nemotron-3-super'],['Harness / version','OpenClaw 2026.9.7','OpenClaw 2026.9.7'],['Temperature / fallback','0 / none','0 / none'],['Reasoning control','medium effort','thinking enabled; high compatibility alias'],['Declared context','65,536 tokens','65,536 tokens'],['Per-response output allowance','4,096 tokens','4,096 tokens'],['Cumulative per-attempt allowance','200,000 conservative input; 16,000 output','Same'],['Physical transmissions per attempt','At most 30, including transport retries','Same'],['Wall deadline','min(original task timeout, 600 seconds)','Same'],['Grading','Original deterministic oracle + fixture integrity','Same']], [CW*.35,CW*.32,CW*.33])
    p('Input admission uses a conservative UTF-8 byte bound with framing, reconciled to reported usage after each settled call. It can stop an attempt before 200,000 actual input tokens have been consumed. A budget stop is retained as a scored outcome. Unknown usage retains its full reservation; it is not assigned zero cost.')
    p('Strict full completion requires a completed status, original score ≥ 0.9999, all exposed checks passing and no integrity violation. A budget-exhausted run can score 100 for its saved artifacts without qualifying as a strict full completion. Fractional original scores remain fractional even if threshold-based checks all pass.')
    p('The two reasoning controls have different semantics and the models have different architectures; the experiment does not establish equal reasoning compute. Nemotron’s listed tool/thinking support and compatibility interface are documented by Ollama [2,3]. Our checks verify this installed harness path rather than assuming a model-name change is sufficient.')

    page('3. What the aggregate scores show')
    fig('01_mean_scores',245,'Figure 1. Original oracle means on the 50 matched tasks. Scores remain on a 0-100 scale; no infrastructure outcome is imputed as zero.')
    table([['Instruction','GPT-OSS mean','Nemotron mean','Paired gain, pp']]+[[langnames[l],f'{val("oss",l):.2f}',f'{val("nemotron",l):.2f}',f'{s["contrasts"]["model_"+l]["mean_difference_pp"]:+.2f}'] for l in LANGS])
    ranked=sorted(LANGS,key=lambda l:val('nemotron',l)-val('oss',l),reverse=True)
    p(f"The largest observed model gap is in <b>{langnames[ranked[0]]}</b>. That identifies a useful follow-up comparison, but it does not explain the cause. Language understanding, tool selection, output-path handling, reasoning allocation and task-specific grading can all contribute to the measured score.")
    fig('02_full_completion',190,'Figure 2. Strict full completions. Labels show counts out of 50; process completion alone does not count as task success.')
    p('Full completion is a more demanding outcome than a high partial score. The two measures should be reported together in the mid-semester report: the score summarizes graded progress, while strict completion checks whether the entire saved outcome meets the protocol.','small')

    page('4. Paired model differences and uncertainty')
    fig('03_model_contrasts',210,'Figure 3. Paired score differences with percentile 95% task bootstrap intervals. Six conditions remain together when a task is resampled; 10,000 resamples, seed 20260930.')
    p(f"Averaging the three language differences within each task gives an overall gain of <b>{ci(overall)} pp</b>. The interval is {'entirely above zero' if overall['ci'][0]>0 else 'not entirely above zero'} in this exploratory analysis. This is an estimate for the selected benchmark population, not a causal estimate of model architecture or a general multilingual ability claim.")
    table([['Comparison','Nemotron higher','Tie','GPT-OSS higher']]+[[langnames[l],s['contrasts']['model_'+l]['wins'],s['contrasts']['model_'+l]['ties'],s['contrasts']['model_'+l]['losses']] for l in LANGS]+[['Task mean',overall['wins'],overall['ties'],overall['losses']]])
    fig('04_paired_scores',160,'Figure 4. One point per task in each language. Points above the diagonal favor Nemotron; orange points are the four additions. Overlapping points can hide ties.')
    p('Intervals are descriptive and unadjusted for the several contrasts examined. The report avoids treating individual non-zero intervals as confirmatory significance tests. A future paper should state a primary contrast and use an appropriate multiplicity policy before a new campaign.','small')

    page('5. Instruction language within each model')
    fig('05_language_contrasts',260,'Figure 5. English minus Hindi/Hinglish paired score differences. Negative values favor the other instruction language. Intervals use 50 task clusters.')
    table([['Model','English - Hindi, pp [95% interval]','English - Hinglish, pp [95% interval]']]+[[names[m],ci(s['contrasts'][m+'_en_minus_hi']),ci(s['contrasts'][m+'_en_minus_hinglish'])] for m in MODELS],[CW*.24,CW*.38,CW*.38])
    p('These contrasts directly address the language-degradation question. A positive estimate means English scored higher on average; a negative estimate means Hindi or Hinglish scored higher. When an interval includes zero, the measured task-to-task variation does not support a clear directional conclusion under this analysis.')
    p('Hindi exceeds English by 5.91 points for GPT-OSS and 2.59 points for Nemotron. English exceeds Hinglish by 5.82 and 1.92 points respectively. All four intervals include zero. The larger Hinglish model gap describes a difference between configurations; it is not evidence that changing instruction language caused that gap.','small')
    p('Context tokens are a separate descriptive measurement','h2')
    table([['Model / instruction','Mean first-context ratio to English','Paired tasks measured']]+[[names[m]+' / '+langnames[l],f"{s['contrasts'][m+'_en_minus_'+l]['mean_first_context_ratio']:.3f}",s['contrasts'][m+'_en_minus_'+l]['first_context_ratio_n']] for m in MODELS for l in ['hi','hinglish']],[CW*.45,CW*.35,CW*.2])
    p('These ratios include the OpenClaw system prompt, tool schemas and framing. They do not isolate the translated instruction’s tokenization. Even a larger Hindi context count would not establish that tokenization caused a score difference. The translations were self-reviewed by AI and have not received independent bilingual human review.')

    page('6. Differences across task families')
    fig('06_categories',305,'Figure 6. Category means across all three languages. Every task receives equal weight. Family sample sizes are small and shown explicitly.')
    strongest=max(s['categories'],key=lambda c:c['difference_pp']);weakest=min(s['categories'],key=lambda c:c['difference_pp'])
    p(f"The largest observed family-level gain appears in <b>{escape(short(strongest['category']))}</b> ({strongest['difference_pp']:+.1f} pp); the weakest difference appears in <b>{escape(short(weakest['category']))}</b> ({weakest['difference_pp']:+.1f} pp). These comparisons help identify where to inspect traces, but they are exploratory and sensitive to the particular tasks in each family.")
    p('The benchmark is heterogeneous. Some tasks reward exact files and schemas; others score evidence coverage, planning decisions or partial code repair. A single aggregate score can conceal a model’s strong document synthesis and weak filesystem execution, or the opposite. Category and per-task views are therefore retained alongside the overall comparison.')
    p('The original Harness-Bench frames the evaluated unit as a model-harness configuration and records artifacts and traces to diagnose execution behavior [1]. This extension follows that framing. It evaluates the installed OpenClaw configuration and its secured runtime, rather than attributing every observed failure to the base model alone.')

    page('7. Resource use and practical efficiency')
    fig('07_resources',230,'Figure 7. Distributions across the 150 selected outcomes per model. Boxes show quartiles and medians; outlier dots are omitted. Known tokens exclude unmeasured usage, whose reservations remain charged separately.')
    table([['Model / language','Median elapsed, sec','Median known input','Median known output']]+[[names[m]+' / '+langnames[l],f'{val(m,l,"median_elapsed_sec"):.1f}',f'{val(m,l,"median_known_input"):,.0f}',f'{val(m,l,"median_known_output"):,.0f}'] for m in MODELS for l in LANGS],[CW*.36,CW*.2,CW*.22,CW*.22])
    p('Elapsed time includes harness startup, agent work, local hooks, artifact extraction and grading. It is not pure provider inference latency. Token totals include repeated context across tool calls and measured reasoning where the provider includes it in output usage.')
    p('The score comparison is not a monetary cost ranking. This campaign uses free allowance only and records no automatic purchase. Account-specific remaining allowance, effective billing and whether the four credentials share quota are not inferred from token counts. No claim that Nemotron is cheaper is supported by these measurements.')

    page('8. Infrastructure, retries and accounting')
    account=s['accounting_all_campaign_attempts']
    table([['All campaign records, incl. excluded tasks','GPT-OSS','Nemotron'],['Primary attempts',account['oss']['primary_attempts'],account['nemotron']['primary_attempts']],['Fresh recovery attempts',account['oss']['recovery_attempts'],account['nemotron']['recovery_attempts']],['Terminal INFRA attempts',account['oss']['status_counts'].get('infrastructure_failed',0),account['nemotron']['status_counts'].get('infrastructure_failed',0)],['Physical transmissions',f"{account['oss']['physical_transmissions']:,}",f"{account['nemotron']['physical_transmissions']:,}"],['Known input tokens',f"{account['oss']['known_input']:,}",f"{account['nemotron']['known_input']:,}"],['Conservatively charged input',f"{account['oss']['charged_input']:,}",f"{account['nemotron']['charged_input']:,}"],['Known output tokens',f"{account['oss']['known_output']:,}",f"{account['nemotron']['known_output']:,}"],['Conservatively charged output',f"{account['oss']['charged_output']:,}",f"{account['nemotron']['charged_output']:,}"],['Settled calls with missing usage',account['oss']['usage_missing_calls'],account['nemotron']['usage_missing_calls']]],[CW*.56,CW*.22,CW*.22])
    p(f"This table is an operational ledger, not the 300-condition statistical population. It includes the original excluded GPT-OSS tasks and all saved fresh recoveries. Compatibility/probe spending is recorded separately and excluded from these benchmark totals. The original OSS ledger retains <b>{account['oss']['unsettled_reservations']} unsettled reservation(s)</b>, conservatively charged. Nemotron retains {account['nemotron']['unsettled_reservations']}. No old accounting is rewritten to make the table look complete.")
    p('Nemotron originally saved five primary INFRA outcomes. Three first recoveries were scored; two remained INFRA and later received one more explicitly authorized attempt each. All seven fresh attempts remain in the history. The final main view substitutes the first scored recovery after an infrastructure failure, even when its score is zero. It never selects the best score among retries.')
    p('For the four additions, both models receive the same bounded policy: at most two fresh recoveries, only after terminal INFRA. Generic rate limits, timeouts and model failures do not trigger credential rotation; only confirmed quota exhaustion does. Saved checkpoints and full unknown reservations survive interruption. Sustained provider trouble holds future admissions rather than consuming allowance indefinitely.')

    page('9. The four additions')
    p('These tasks extend the existing comparison to 50 distinct task units. They use the same English source instructions, fixtures, translation versions and original graders for both models. No original condition was rerun. Storage is append-only under the parent study identities, with separate attempt provenance for auditability.')
    table([['Task','OSS EN / HI / HG','Nemotron EN / HI / HG']]+[[r['task_id'].split('-',1)[0]+' · '+r['task_id'].split('-',1)[1].replace('-',' '),' / '.join(f'{r["oss_"+l]:.1f}' for l in LANGS),' / '.join(f'{r["nemotron_"+l]:.1f}' for l in LANGS)] for r in atlas if r['added']],[CW*.48,CW*.26,CW*.26])
    p('All <b>24/24 new primary conditions</b> produced saved, scored outcomes: GPT-OSS had five completed processes and seven budget stops; Nemotron had eleven completed processes and one budget stop. There were <b>zero new INFRA outcomes, zero fresh recoveries and zero missing-usage calls</b>. Low scores are retained as agent outcomes; none were retried for improvement.')
    ext=s['extension_accounting']
    p(f"The additions recorded {ext['transmissions']:,} physical transmissions, {ext['known_input']:,} input tokens and {ext['known_output']:,} output tokens. Conservative charges equal these measured totals, and all new reservations settled. Historical unknown usage remains in the separate full campaign ledger.",'small')
    p('Selection and validation','h2')
    p('Inventory forecasting exercises arithmetic, boundary decisions and a consistent exception ledger. The reproducibility audit requires honest identification of missing data and broken automation. A/B analysis checks statistics and caveats. Release approval planning requires a blocked decision, evidence-linked blockers and proposed actions without false execution claims. All four passed private correct-output and negative validation inside restricted containers before inference.')
    p('Windows fixture text is normalized to Unix line endings only in the private grader image, using the original baseline’s build procedure. This makes embedded original fixture hashes match without changing source files or oracle logic. All instruction languages receive the same canonical fixture bytes.')
    p('Runtime disclosure','h2')
    p('The additions use the repaired streaming relay for both models and an explicit provider watchdog bounded by the unchanged whole-attempt deadline. GPT-OSS retains medium effort; Nemotron retains enabled boolean thinking through its high compatibility alias. Historical GPT-OSS transport used a shorter buffered path. Thus this is one extended study with a documented runtime revision, not a claim that the earlier and added executions were byte-identical.')

    page('10. What the traces explain')
    p('A concrete output-path failure','h2')
    p('In the new GPT-OSS Hindi inventory attempt, the tool trace shows output files written under a relative <b>workspace/out</b> directory inside the workspace. The contract required <b>/workspace/out</b>. The saved snapshot therefore contains the proposed deliverables in the wrong location, while the required output directory lacks them. The agent nevertheless reported that the files had been generated. The original oracle scored 9.47/100; transport usage was measured and no INFRA retry was justified.')
    p('This distinguishes execution alignment from pure arithmetic. A plausible explanation and apparently correct numbers are insufficient when the verified artifact contract is unmet. The trace also contains literal escape sequences in generated file content. No path repair or content unescaping was applied after the attempt, because that would change the evaluated agent outcome.')
    p('Evidence and artifact contracts recur in both models','h2')
    table([['Model','Most frequent failed exposed checks']]+[[names[m],'; '.join(f'{escape(str(k))} ({n})' for k,n in s['most_frequent_failed_checks'][m][:7])] for m in MODELS],[CW*.25,CW*.75])
    p('These counts come from failed grader checks among the selected 150 outcomes per model. They are diagnostic, not independent failure events: one missing file can cause several checks to fail, and check IDs are not necessarily shared across every task. They should guide trace inspection rather than be interpreted as a universal failure rate.')
    p('A stronger follow-up paper would annotate a blinded, predetermined trace sample for wrong paths, malformed arguments, unsupported completion claims, missing evidence and partial completion. That would test whether the observed categories explain the score gaps; the present report does not claim that attribution has already been established.')

    page('11. Sensitivity to recovery and expansion')
    prim=s['primary_only'];old=s['old46_models'];new=s['additions_models']
    data=[['Population / view','Tasks','OSS EN / HI / HG','Nemotron EN / HI / HG']]
    for label,n,stats in [('Combined resolved view',50,s['models']),('Common primary-only complete cases',prim['task_count'],prim['models']),('Retained portion of this study',46,old),('Four added tasks',4,new)]:data.append([label,n,' / '.join(f'{stats["oss"][l]["mean_score"]:.2f}' for l in LANGS),' / '.join(f'{stats["nemotron"][l]["mean_score"]:.2f}' for l in LANGS)])
    table(data,[CW*.34,CW*.08,CW*.29,CW*.29])
    p(f"The common primary-only view contains <b>{prim['task_count']} tasks</b>, excluding any task with an unscored primary outcome in either model/language. Its task-average paired model difference is <b>{ci(prim['contrasts']['model_overall'])} pp</b>. This comparison addresses the unequal historical recovery opportunity without assigning infrastructure failure a score of zero.")
    p('Task IDs excluded from the common primary-only view: '+', '.join(prim['excluded_task_ids'])+'.','small')
    p('The retained portion and four additions are shown to make the expansion’s influence visible. They are portions of the same study, not independent replications. The four-task portion is too small to support a standalone language conclusion. Selection occurred after prior outcomes, so this sensitivity cannot convert the full study into a preregistered confirmatory design.')
    p('The original 46-task OSS analysis and PDF remain the authoritative historical baseline record. The combined report adds evidence without silently reclassifying the original eight excluded task groups or replacing previous low scores. The original Nemotron primary-only and earlier recovery views are also preserved.')

    page('12. Limits and claims for the paper')
    p('What the data support','h2')
    p('The team can report a paired comparison on 50 distinct local agent tasks with 150 scored conditions per model. It can report the observed means, completion counts, task-cluster intervals, category variation and infrastructure history. It can state whether the directional language-degradation hypothesis is consistent with each measured contrast, including results that favor Hindi or show uncertainty.')
    p('What remains unresolved','h2')
    for text in [
      '<b>Scope and sampling.</b> This is a selected offline subset, expanded after earlier outcomes. It is not representative sampling of all Indian-language agent tasks. Fixtures and prose outputs remain English.',
      '<b>Translation validity.</b> Hindi is written in Devanagari; Hinglish uses Romanized Hindi mixed with English. Translations are AI-authored/self-reviewed, not independently human validated. Literal schemas and output strings remain fixed.',
      '<b>Stochastic variation.</b> One primary trajectory per task/language/model does not estimate repeat-run reliability. Temperature zero does not establish deterministic managed-cloud execution.',
      '<b>Configuration confounding.</b> Models, reasoning controls, native tool behavior, managed-cloud weights and transport revisions differ. A larger model score is not an isolated architecture effect, and a language gap is not proof of tokenizer causality.',
      '<b>Grader interpretation.</b> Original deterministic scores may award partial credit for artifact presence or keyword coverage. They are task-specific proxies; threshold checks can pass without a score of 100. No new LLM judge validates semantic correctness.',
      '<b>Recovery and attrition.</b> The resolved comparison incorporates scored Nemotron infrastructure recoveries; OSS uses the historical whole-task primary exclusion. The common primary-only sensitivity is required when discussing that asymmetry.',
      '<b>Uncertainty and multiplicity.</b> Bootstrap intervals quantify variation across these task clusters. They are exploratory, unadjusted for multiple comparisons and do not address systematic selection or translation bias.'
    ]:p(text)
    p('Suggested framing: “A controlled instruction-language comparison of two OpenClaw model configurations on 50 matched offline tasks.” Broader claims about general Hindi capability, causal degradation or model cost efficiency require additional evidence.','small')

    page('13. Reproducibility and containment')
    p('All evaluated agent processes, shell commands, hooks and graders ran inside hardened Docker. Agent containers ran as a non-root user with a read-only root filesystem, dropped capabilities, no-new-privileges, resource caps and a restricted internal network. They received no host bind mounts, Docker control interfaces, real credentials or private oracle solutions. Grading occurred in a separate no-network container after the agent stopped.')
    p('The trusted controller used kernel-exclusive leases, transactional SQLite WAL with synchronous FULL, reservations before forwarding, durable response settlement, bounded traces, atomic exports and online checkpoints. Keys remained in the encrypted credential store and were passed only to the trusted relay. Cleanup operated only on recorded ownership-verified resource identities. These controls are part of the method, not an assertion that the evaluated model would behave safely without containment.')
    p('Reusable artifacts','h2')
    table([['Artifact under output/pdf/','Purpose'],['report_data/matched_conditions.csv and .json','300 selected condition records; IDs, scores, usage and provenance'],['report_data/task_score_atlas.csv','50 task rows × six scores'],['report_data/analysis_summary.json','Means, paired intervals, categories and sensitivity'],['report_data/all_campaign_attempts.csv','Full operational attempt ledger, including excluded tasks'],['report_data/infrastructure_history.csv','Saved unscored infrastructure/interruption history'],['report_data/task_selection.csv and validation.json','Scope and exact journal reconciliation checks'],['figures/*.png and *.svg','Raster and editable vector research figures'],['scripts/analyze50.py and scripts/report50.py','Editable analysis and report builders in the project']],[CW*.53,CW*.47])
    p('The shared extension directory contains the selection timestamp, translation hashes, original oracle-validation evidence, image pins, canonical fixture-copy record, parent study IDs, frozen execution source hashes and full old-result preservation snapshot. The study can be reviewed by tracing a selected condition ID back to its immutable journal and saved workspace.')
    digest=s['provenance']['extension_freeze'];p('Extension execution freeze: '+'<br/>'.join(digest[i:i+32] for i in range(0,len(digest),32)),'small')
    p('Original OSS PDF SHA-256: '+'<br/>'.join(s['provenance']['original_oss_pdf_sha256'][i:i+32] for i in range(0,64,32)),'small')

    atlas_status={(r['model'],r['task_id'],r['language']):(r['status'],r.get('attempt_number',1)) for r in rows}
    for number,part in enumerate([atlas[:25],atlas[25:]],1):
        page(f'Appendix A{number}. Task score atlas')
        p('Original oracle score / 100. EN = English; HI = Hindi; HG = Hinglish. B = budget-exhausted outcome; R = scored infrastructure recovery. An asterisk marks an added task. Six values on a row belong to one original task.','small')
        data=[['Task','OSS EN','OSS HI','OSS HG','Nem EN','Nem HI','Nem HG']]
        for r in part:
            values=[]
            for m in MODELS:
                for l in LANGS:
                    status,num=atlas_status[m,r['task_id'],l]
                    values.append(f'{r[m+"_"+l]:.1f}'+(' B' if status=='budget_exhausted' else '')+(' R' if num>1 else ''))
            data.append([r['task_id'].split('-',1)[0]+(' *' if r['added'] else '')+' '+r['task_id'].split('-',1)[1].replace('-',' ')]+values)
        table(data,[CW*.40]+[CW*.10]*6,padding=6,space_after=0)
    page('Appendix B. Visual task atlas')
    fig('08_task_heatmap',650,'Figure 8. Six scores per original task. Lighter cells indicate lower scores; darker cells indicate higher scores (0-100). Numbers are rounded only for display; analysis uses saved unrounded values. Asterisks indicate the four added tasks.')
    page('References and review notes')
    refs=[
      ('1','Yao, Y. et al. (2026). Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows. arXiv:2605.27922v1.','https://arxiv.org/abs/2605.27922'),
      ('2','Ollama. Nemotron 3 Super model page. Provider tool/thinking/cloud and model-family description. Retrieved 2 October 2026.','https://ollama.com/library/nemotron-3-super'),
      ('3','Ollama. OpenAI compatibility documentation. Provider interface and reasoning compatibility. Retrieved 2 October 2026.','https://docs.ollama.com/api/openai-compatibility')]
    for n,title,url in refs:p(f'[{n}] {escape(title)}<br/><link href="{url}" color="{BLUE}">{escape(url)}</link>')
    p('Primary experimental sources','h2')
    p('The protected project journals, saved task workspaces, original deterministic graders, the existing 46-task OSS report data, Nemotron’s user-requested resolved exports and the new four-task continuation journals are the primary sources for every numerical result in this report. The provider pages support interface/background statements; they do not validate this experiment’s scores.')
    p('Before using this material in the paper','h2')
    p('Have bilingual reviewers inspect the translated instructions and their literal contracts. Have a teammate independently reproduce the paired statistics from matched_conditions.csv. Review a predetermined trace sample for execution failures. State the historical recovery policy and runtime changes in Methods, retain the primary-only sensitivity, and avoid relabeling condition records as independent task samples.')
    p('No author list, supervisor sign-off, course rubric interpretation, funding claim or publication approval is invented here. Add the team’s names and course formatting after factual review. This working report preserves the prior baseline and provides a documented 50-task dataset for that next step.','small')
    def footer(c,doc):
        c.saveState();w,h=A4;c.setFillColor(HexColor(NAVY));c.setFont('Bold',8);c.drawString(47,h-27,'INDIC HARNESS BENCH');c.setFont('Body',7.5);c.setFillColor(HexColor(GRAY));c.drawRightString(w-47,h-27,'50 matched tasks · research working report');c.setStrokeColor(HexColor('#d6e1e8'));c.line(47,40,w-47,40);c.drawString(47,27,'GPT-OSS-20B / Nemotron 3 Super · 2 October 2026');c.drawRightString(w-47,27,str(doc.page));c.restoreState()
    DEST.mkdir(parents=True,exist_ok=True)
    doc=SimpleDocTemplate(str(PDF),pagesize=A4,rightMargin=47,leftMargin=47,topMargin=52,bottomMargin=53,title='Indic Harness Bench: A matched 50-task model comparison',author='Indic Harness Bench research team',pageCompression=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(PDF);text='\n'.join(p.extract_text() for p in reader.pages)
    checks={'task_count':s['task_count']==50,'condition_count':s['total_scored_conditions']==300,'pdf_readable':len(reader.pages)>=15,'old_pdf_hash_retained':sha(ROOT/'pdf/Indic_Harness_Bench_Experiment_Report.pdf')==s['provenance']['original_oss_pdf_sha256'],'no_placeholder_text':not any(v in text for v in ['TODO','TBD','PLACEHOLDER']),'figures_exist':len(list(FIG.glob('*.png')))==8}
    atomic_json(OUT/'pdf_build_validation.json',{'passed':all(checks.values()),'checks':checks,'pages':len(reader.pages),'pdf_sha256':sha(PDF),'visual_review_pending':True})
    print(json.dumps({'pdf':str(PDF),'pages':len(reader.pages),'checks':checks}))
    if not all(checks.values()):raise ValueError('PDF structural validation failed')

if __name__=='__main__':
    with ControllerLease(SHARED/'results/report.lock'):
        s,rows,atlas=analyze();charts(s,rows,atlas);report(s,rows,atlas)
