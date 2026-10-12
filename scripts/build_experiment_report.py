"""Read-only study analysis and a reproducible, strictly infrastructure-free PDF report."""
from __future__ import annotations
import collections,csv,hashlib,json,math,os,random,re,sqlite3,statistics,sys
from contextlib import closing
from datetime import datetime,timedelta,timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tmp/pdf-report-deps'))
sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from pypdf import PdfReader,PdfWriter
from bench.metrics import attempt_metrics,compare,AGENT_OUTCOMES
from bench.durable import encode
from bench.extension import check_extension
from bench.provenance import verify_reference

OUT=ROOT/'pdf';DATA=OUT/'report_data';FIG=OUT/'figures';TMP=ROOT/'tmp/pdfs/experiment-report'
LANGS=['en','hi','hinglish'];LABEL={'en':'English','hi':'Hindi','hinglish':'Hinglish'}
INK='#19334B';MUTED='#536A7F';TEAL='#007F7A';BLUE='#325EA8';ORANGE='#C27728'
PALETTE=[BLUE,TEAL,ORANGE];LIGHT='#EFF4F8';BORDER='#D8E2EA'
CATS=[
 ('Workspace, Tool Use & Multimodal Operations','Workspace and tools','WT'),
 ('Office & Business Communication','Office and communication','OC'),
 ('Knowledge, Evidence & Retrieval','Knowledge and evidence','KE'),
 ('Software Engineering & Codebase Maintenance','Software engineering','SE'),
 ('Data, BI & Finance Analytics','Data, BI and finance','DF'),
 ('Long-running Autonomy & State Adaptation','State and autonomy','SA'),
 ('SRE, DevOps & Release Ops','SRE and release operations','SR'),
 ('Vertical Professional Workflows','Professional workflows','PW')]
CAT_SHORT={c:s for c,s,_ in CATS};CAT_CODE={c:s for c,_,s in CATS}
IST=timezone(timedelta(hours=5,minutes=30));STAMP=datetime.now(IST)


def read(relative):return json.loads((ROOT/relative).read_text(encoding='utf-8'))
def dump(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def ci(values):
    rng=random.Random(20260930);n=len(values)
    samples=sorted(statistics.mean(rng.choices(values,k=n)) for _ in range(10000))
    return [samples[250],samples[9750]]
def wilson(k,n):
    z=1.96;p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,mid-half),min(1,mid+half)]
def pct(x):return f'{100*x:.2f}'


def collect():
    manifest=read('dataset/task_manifest.json');meta={t['task_id']:t for t in manifest}
    selection=read('dataset/extension_selection.json');freeze=read('dataset/freeze.json')
    class View:pass
    with closing(sqlite3.connect((ROOT/'results/journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row;j=View();j.db=db
        raw=[dict(r) for r in db.execute('SELECT * FROM runs ORDER BY rowid')]
        assert len(raw)==162 and not any(r['status'] in ('planned','running') for r in raw)
        groups={}
        for r in raw:groups.setdefault(r['task'],{})[r['language']]=r
        excluded={t:v for t,v in groups.items() if any(r['status']=='infrastructure_failed' for r in v.values())}
        good={t:v for t,v in groups.items() if t not in excluded and set(v)==set(LANGS) and all(r['status'] in AGENT_OUTCOMES for r in v.values())}
        assert len(good)+len(excluded)==54
        metrics=[attempt_metrics(j,r,meta[r['task']]['category']) for r in raw if r['task'] in good]
        g={t:{l:next(m for m in metrics if m['run_id']==v[l]['id']) for l in LANGS} for t,v in good.items()}
        assert len(metrics)==len(g)*3 and all(m['original_score'] is not None for m in metrics)
        failed=[]
        for task,versions in excluded.items():
            causes=[]
            for lang in LANGS:
                r=versions[lang]
                if r['status']!='infrastructure_failed':continue
                events=[json.loads(e[0]) for e in db.execute("SELECT payload FROM events WHERE run_id=? AND kind='provider_pause' ORDER BY seq",(r['id'],))]
                if any(e.get('stage')=='settlement' for e in events):reason='Local accounting acknowledgment'
                elif any(e.get('stage')=='agent_delivery' for e in events):reason='Response delivery / broken pipe'
                elif any(e.get('classification')=='ambiguous_transport' for e in events):reason='Ambiguous transport / timeout'
                elif any(e.get('classification')=='transient' and e.get('status')==500 for e in events):reason='Provider HTTP 500 after retries'
                else:reason='Other recorded infrastructure gate'
                causes.append({'language':lang,'run_id':r['id'],'cause':reason,'events':events})
            failed.append({'task_id':task,'category':meta[task]['category'],'failed_languages':[c['language'] for c in causes],
                'cause':' / '.join(dict.fromkeys(c['cause'] for c in causes)), 'causes':causes})
        included_ids=[m['run_id'] for m in metrics]
        budget=[];cases={};symptoms=collections.Counter();check_pass_below_one=0
        for m in metrics:
            r=next(r for r in raw if r['id']==m['run_id']);result=json.loads(r['result']);checks=result.get('oracle',{}).get('checks',[])
            failures=[c for c in checks if not c.get('pass')]
            missing=False
            for c in failures:
                d=str(c.get('detail','')).lower().strip();lab=str(c.get('label','')).lower()
                identifier=str(c.get('id','')).lower()
                if ('no such file' in d or 'filenotfounderror' in d
                    or (d=='missing' and ('exists' in lab or 'exists' in identifier))
                    or re.fullmatch(r'(?:missing\s+[^\n]+\.(?:csv|json|txt|md)|[^\n]+\.(?:csv|json|txt|md)\s+missing)',d)):
                    missing=True
            if missing:symptoms['missing_artifact_conditions']+=1
            if m['original_score']==0:symptoms['zero_score_conditions']+=1
            if checks and all(c.get('pass') for c in checks) and m['original_score']<1:check_pass_below_one+=1
            if m['status']=='budget_exhausted':
                events=[json.loads(e[0]) for e in db.execute("SELECT payload FROM events WHERE kind='budget_denied' AND run_id=? ORDER BY seq",(m['run_id'],))]
                reason=events[-1].get('reason','unavailable') if events else 'unavailable'
                trigger='Output allowance' if 'output' in reason.lower() else 'Input preflight allowance' if 'input' in reason.lower() else 'Other'
                budget.append({'task_id':m['task_id'],'language':m['language'],'reason':reason,'trigger':trigger})
            if m['task_id'] in ('005-email-triage','063-alert-dedup-noise','034-evidence-matrix-claims','035-conflicting-source-resolution','028-email-thread-merge','062-k8s-config-audit'):
                cases.setdefault(m['task_id'],{})[m['language']]={'score':m['original_score'],'status':m['status'],'failures':failures}
        slots=dict(db.execute('SELECT slot,COUNT(*) FROM forwards GROUP BY slot'))
        all_totals={'requests':sum(r['requests'] for r in raw),'known_input':sum(r['input_actual'] for r in raw),'known_output':sum(r['output_actual'] for r in raw)}
        start=min(r['started'] for r in raw);finish=max(r['finished'] for r in raw)
        run_digest=hashlib.sha256(encode(raw).encode()).hexdigest()
    summary={}
    for lang in LANGS:
        ms=[m for m in metrics if m['language']==lang];scores=[m['original_score'] for m in ms]
        summary[lang]={'n':len(ms),'mean':statistics.mean(scores),'mean_ci':ci(scores),'median':statistics.median(scores),
            'full':sum(m['full_completion'] for m in ms),'full_rate':statistics.mean(m['full_completion'] for m in ms),
            'full_rate_wilson':wilson(sum(m['full_completion'] for m in ms),len(ms)),
            'zero':sum(m['original_score']==0 for m in ms),'budget':sum(m['status']=='budget_exhausted' for m in ms),
            'median_sec':statistics.median(m['elapsed_sec'] for m in ms),'mean_sec':statistics.mean(m['elapsed_sec'] for m in ms),
            'known_input':sum(m['known_input_tokens'] for m in ms),'known_output':sum(m['known_output_tokens'] for m in ms),
            'uncertain_usage':sum(m['usage_uncertain'] for m in ms),'requests':sum(m['physical_requests'] for m in ms),
            'tool_calls':sum(m['tool_calls'] or 0 for m in ms),'transport_retries':sum(m['transport_retries'] for m in ms)}
    ratios={}
    for lang in ['hi','hinglish']:
        byte=[];char=[];first=[]
        for task,v in g.items():
            prompts=meta[task]['source_prompt_files']
            en=''.join((ROOT/'tasks'/task/'prompts/en'/p).read_text(encoding='utf-8') for p in prompts)
            target=''.join((ROOT/'tasks'/task/'prompts'/lang/p).read_text(encoding='utf-8') for p in prompts)
            byte.append(len(target.encode())/len(en.encode()));char.append(len(target)/len(en))
            if v['en']['first_context_prompt_tokens'] and v[lang]['first_context_prompt_tokens']:
                first.append(v[lang]['first_context_prompt_tokens']/v['en']['first_context_prompt_tokens'])
        ratios[lang]={'mean_prompt_byte_ratio':statistics.mean(byte),'mean_prompt_character_ratio':statistics.mean(char),'mean_first_context_token_ratio':statistics.mean(first)}
    cohorts={}
    for name,ids in [('Initial 40',selection['original_task_ids']),('Added 14',selection['selected_task_ids'])]:
        tasks=[t for t in g if t in ids]
        cohorts[name]={'retained':len(tasks),'scheduled':len(ids),'mean_scores':{l:statistics.mean(g[t][l]['original_score'] for t in tasks) for l in LANGS}}
    wins={}
    for lang in ['hi','hinglish']:
        ds=[v[lang]['original_score']-v['en']['original_score'] for v in g.values()]
        wins[lang]={'higher':sum(d>1e-6 for d in ds),'tied':sum(abs(d)<=1e-6 for d in ds),'lower':sum(d< -1e-6 for d in ds)}
    data={'generated_ist':STAMP.isoformat(),'filter':'Exclude entire original task if any primary language condition has status infrastructure_failed; do not substitute retries.',
        'scheduled_tasks':54,'primary_attempts':162,'primary_status_counts':dict(collections.Counter(r['status'] for r in raw)),
        'included_tasks':len(g),'included_conditions':len(metrics),'excluded_tasks':failed,'retained_instruction_turns':sum(len(meta[t]['source_prompt_files']) for t in g),
        'summary':summary,'analysis':compare(metrics),'categories':{c:{'n':sum(meta[t]['category']==c for t in g),
            'mean_scores':{l:statistics.mean(v[l]['original_score'] for t,v in g.items() if meta[t]['category']==c) for l in LANGS}} for c,_,_ in CATS},
        'cohorts':cohorts,'paired_rank_counts':wins,'prompt_ratios':ratios,'budget_events':budget,'symptoms':dict(symptoms),
        'all_checks_pass_score_below_one':check_pass_below_one,'cases':cases,'included_metrics':metrics,
        'included_task_ids':list(g),'freeze':{k:v for k,v in freeze.items() if k!='file_hashes'},'protocol':read('config/protocol.json'),
        'runtime_counts':dict(collections.Counter(m['runtime_freeze_hash'] for m in metrics)),
        'primary_forward_slots':slots,'primary_usage_totals':all_totals,'primary_start_ist':datetime.fromtimestamp(start,IST).isoformat(),
        'primary_end_ist':datetime.fromtimestamp(finish,IST).isoformat(),'primary_run_records_sha256':run_digest,
        'retry':read('results/infrastructure_retries.json'),'references':verify_reference(),'preservation':check_extension()}
    return data,g,meta


def plots(d,g):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelcolor':INK,'text.color':INK,
        'axes.edgecolor':BORDER,'xtick.color':MUTED,'ytick.color':MUTED,'axes.titleweight':'bold',
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white'})
    paths={}
    def save(name,fig):
        fig.savefig(FIG/(name+'.png'),dpi=240,bbox_inches='tight',facecolor='white')
        fig.savefig(FIG/(name+'.svg'),bbox_inches='tight',facecolor='white')
        plt.close(fig);paths[name]=FIG/(name+'.png')
    s=d['summary'];n=d['included_tasks'];x=np.arange(3)
    fig,axs=plt.subplots(1,2,figsize=(8,3.1),layout='constrained')
    for ax,key,title,maxv in [(axs[0],'mean','Mean oracle score',100),(axs[1],'full_rate','Full completion rate',30)]:
        vals=np.array([100*s[l][key] for l in LANGS]);intervals=np.array([s[l]['mean_ci' if key=='mean' else 'full_rate_wilson'] for l in LANGS])*100
        ax.bar(x,vals,color=PALETTE,width=.55,zorder=3);ax.errorbar(x,vals,yerr=np.array([vals-intervals[:,0],intervals[:,1]-vals]),fmt='none',ecolor=INK,capsize=4,zorder=4)
        ax.set_xticks(x,[LABEL[l] for l in LANGS]);ax.set_ylim(0,maxv);ax.set_title(title,loc='left',fontsize=12,pad=14)
        ax.set_ylabel('Score / 100' if key=='mean' else 'Percent of tasks');ax.yaxis.grid(True,color=LIGHT);ax.set_axisbelow(True)
        for i,v in enumerate(vals):ax.text(i,v+1.1,f'{v:.1f}',ha='center',va='bottom',fontsize=10,fontweight='bold')
    save('overall',fig)
    estimates=[e for e in d['analysis']['estimates'] if e['category']=='all']
    fig,ax=plt.subplots(figsize=(8,2.6),layout='constrained')
    for i,e in enumerate(estimates):
        mean=e['score_difference_pp'];low,high=e['score_bootstrap_95_percent_interval_pp']
        ax.errorbar(mean,1-i,xerr=[[mean-low],[high-mean]],fmt='o',markersize=9,color=PALETTE[i+1],capsize=6,lw=2)
        ax.text(high+1,1-i,f'{mean:+.2f} pp',va='center',fontsize=10,fontweight='bold')
    ax.axvline(0,color=MUTED,lw=1,ls='--');ax.set_yticks([1,0],['English minus Hindi','English minus Hinglish']);ax.set_xlim(-24,24);ax.set_ylim(-.6,1.6)
    ax.set_xlabel('Mean paired score difference (percentage points)');ax.xaxis.grid(True,color=LIGHT)
    save('paired_intervals',fig)
    fig,axs=plt.subplots(1,2,figsize=(8,3.6),layout='constrained')
    for ax,l,col in zip(axs,['hi','hinglish'],PALETTE[1:]):
        points=collections.Counter((round(v['en']['original_score'],5),round(v[l]['original_score'],5)) for v in g.values())
        ax.scatter([p[0] for p in points],[p[1] for p in points],s=[32+22*k for k in points.values()],color=col,alpha=.72,edgecolors='white',linewidth=.5,zorder=3)
        ax.plot([0,1],[0,1],color=MUTED,ls='--',lw=1);ax.set_xlim(-.04,1.05);ax.set_ylim(-.04,1.05)
        ax.set_xlabel('English score');ax.set_ylabel(LABEL[l]+' score');ax.set_title(LABEL[l]+' vs English',loc='left',fontsize=11);ax.set_aspect('equal');ax.grid(color=LIGHT,zorder=0)
    save('paired_scatter',fig)
    fig,ax=plt.subplots(figsize=(8,4.3),layout='constrained');y=np.arange(8);height=.23
    for i,l in enumerate(LANGS):
        values=[100*d['categories'][c]['mean_scores'][l] for c,_,_ in CATS]
        ax.barh(y+(i-1)*height,values,height=height,color=PALETTE[i],label=LABEL[l],zorder=3)
    ax.set_yticks(y,[f'{short} (n={d["categories"][cat]["n"]})' for cat,short,_ in CATS]);ax.invert_yaxis();ax.set_xlim(0,100)
    ax.set_xlabel('Mean oracle score / 100');ax.xaxis.grid(True,color=LIGHT);ax.set_axisbelow(True);ax.legend(ncol=3,frameon=False,loc='lower right')
    save('categories',fig)
    fig,ax=plt.subplots(figsize=(8,2.5),layout='constrained')
    left=np.zeros(2)
    for key,col,label in [('higher',TEAL,'Indic score higher'),('tied','#A2B4C2','Tied'),('lower',ORANGE,'English score higher')]:
        vals=[d['paired_rank_counts'][l][key] for l in ['hi','hinglish']]
        ax.barh([1,0],vals,left=left,height=.48,color=col,label=label)
        for i,v in enumerate(vals):ax.text(left[i]+v/2,1-i,str(v),ha='center',va='center',color='white' if key!='tied' else INK,fontweight='bold')
        left+=vals
    ax.set_yticks([1,0],['Hindi vs English','Hinglish vs English']);ax.set_xlim(0,n);ax.set_xlabel('Number of original tasks');ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,1.3),frameon=False,fontsize=9)
    save('wins',fig)
    fig,axs=plt.subplots(1,2,figsize=(8,3.2),layout='constrained')
    durations=[[m['elapsed_sec'] for m in d['included_metrics'] if m['language']==l] for l in LANGS]
    box=axs[0].boxplot(durations,tick_labels=[LABEL[l] for l in LANGS],patch_artist=True,showfliers=True,widths=.45)
    for b,c in zip(box['boxes'],PALETTE):b.set(facecolor=c,alpha=.75)
    axs[0].set_ylabel('Elapsed seconds');axs[0].set_title('Attempt duration',loc='left',fontsize=12);axs[0].yaxis.grid(True,color=LIGHT)
    vals=[s[l]['budget'] for l in LANGS];axs[1].bar(x,vals,color=PALETTE,width=.5,zorder=3);axs[1].set_xticks(x,[LABEL[l] for l in LANGS]);axs[1].set_ylim(0,10)
    axs[1].set_title('Budget-exhausted outcomes',loc='left',fontsize=12);axs[1].set_ylabel('Conditions / 46');axs[1].yaxis.grid(True,color=LIGHT)
    for i,v in enumerate(vals):axs[1].text(i,v+.2,str(v),ha='center',fontweight='bold')
    save('resources',fig)
    fig,axs=plt.subplots(1,2,figsize=(8,3.1),layout='constrained')
    for ax,kind,title in [(axs[0],'known_input','Known input tokens'),(axs[1],'known_output','Known output tokens')]:
        vals=[s[l][kind]/1000000 for l in LANGS];ax.bar(x,vals,color=PALETTE,width=.5,zorder=3)
        ax.set_xticks(x,[LABEL[l] for l in LANGS]);ax.set_title(title,loc='left',fontsize=12);ax.set_ylabel('Million tokens');ax.yaxis.grid(True,color=LIGHT)
        ax.set_ylim(0,max(vals)*1.2)
        for i,v in enumerate(vals):ax.text(i,v+max(vals)*.025,f'{v:.3f}',ha='center',fontsize=9,fontweight='bold')
    save('tokens',fig)
    cmap=LinearSegmentedColormap.from_list('indic',['#F1F5F8','#71C4B9','#00746D'])
    tasks=sorted(g,key=lambda t:int(t.split('-')[0]))
    for page,ts in enumerate([tasks[:23],tasks[23:]],1):
        matrix=np.array([[g[t][l]['original_score'] for l in LANGS] for t in ts])
        fig,ax=plt.subplots(figsize=(8,7.7));fig.subplots_adjust(left=.49,right=.95,top=.96,bottom=.04)
        ax.imshow(matrix,cmap=cmap,vmin=0,vmax=1,aspect='auto');ax.set_xticks(range(3),[LABEL[l] for l in LANGS]);ax.xaxis.tick_top()
        ax.set_yticks(range(len(ts)),[t for t in ts],fontsize=9.2)
        ax.tick_params(axis='both',length=0,pad=7);ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,len(ts),1),minor=True)
        ax.grid(which='minor',color='white',linewidth=2);ax.tick_params(which='minor',bottom=False,left=False)
        for i,t in enumerate(ts):
            for j,l in enumerate(LANGS):
                value=matrix[i,j];suffix='*' if g[t][l]['status']=='budget_exhausted' else ''
                ax.text(j,i,f'{value:.2f}{suffix}',ha='center',va='center',fontsize=10,color='white' if value>.66 else INK)
        for spine in ax.spines.values():spine.set_visible(False)
        save('task_atlas_'+str(page),fig)
    return paths


def report(d,g,meta,figs):
    fonts=Path('C:/Windows/Fonts')
    pdfmetrics.registerFont(TTFont('Segoe',str(fonts/'segoeui.ttf')))
    pdfmetrics.registerFont(TTFont('SegoeBold',str(fonts/'segoeuib.ttf')))
    pdfmetrics.registerFontFamily('Segoe',normal='Segoe',bold='SegoeBold',italic='Segoe',boldItalic='SegoeBold')
    W,H=A4;CW=W-92
    styles={
      'body':ParagraphStyle('Body',fontName='Segoe',fontSize=9.4,leading=13.5,textColor=colors.HexColor(INK),spaceAfter=7),
      'small':ParagraphStyle('Small',fontName='Segoe',fontSize=8,leading=11,textColor=colors.HexColor(MUTED),spaceAfter=5),
      'h1':ParagraphStyle('H1',fontName='SegoeBold',fontSize=23,leading=29,textColor=colors.HexColor(INK),spaceAfter=12),
      'h2':ParagraphStyle('H2',fontName='SegoeBold',fontSize=12,leading=16,textColor=colors.HexColor(TEAL),spaceBefore=8,spaceAfter=6),
      'tag':ParagraphStyle('Tag',fontName='SegoeBold',fontSize=8,leading=11,textColor=colors.HexColor(TEAL),spaceAfter=7),
      'white':ParagraphStyle('White',fontName='Segoe',fontSize=11,leading=16,textColor=colors.white,spaceAfter=8),
      'cover':ParagraphStyle('Cover',fontName='SegoeBold',fontSize=34,leading=40,textColor=colors.white,spaceAfter=12),
      'cell':ParagraphStyle('Cell',fontName='Segoe',fontSize=8.3,leading=11,textColor=colors.HexColor(INK)),
      'cellhead':ParagraphStyle('Cellhead',fontName='SegoeBold',fontSize=8.3,leading=11,textColor=colors.white),
      'callout':ParagraphStyle('Callout',fontName='SegoeBold',fontSize=11,leading=16,textColor=colors.HexColor(INK),spaceAfter=8)}
    story=[]
    def p(text,style='body'):return Paragraph(text,styles[style])
    def para(text,style='body'):story.append(p(text,style))
    def heading(tag,title):
        story.append(PageBreak());para(tag.upper(),'tag');para(title,'h1')
    def table(headers,rows,widths=None,small=False):
        vals=[[p(str(x),'cellhead') for x in headers]]+[[p(escape(str(x)) if not str(x).startswith('<') else str(x),'cell') for x in row] for row in rows]
        t=Table(vals,colWidths=widths or [CW/len(headers)]*len(headers),hAlign='LEFT',repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(INK)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor(LIGHT)]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),6 if small else 8),('BOTTOMPADDING',(0,0),(-1,-1),6 if small else 8),
            ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor(INK))]))
        story.append(t);story.append(Spacer(1,9))
    def image(name,width=CW,height=None):
        im=Image(str(figs[name]));ratio=im.imageHeight/im.imageWidth
        story.append(Image(str(figs[name]),width=width,height=height or width*ratio));story.append(Spacer(1,5))
    def caption(text):para(text,'small')
    def callout(text):
        t=Table([[p(text,'callout')]],colWidths=[CW]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(LIGHT)),('BOX',(0,0),(-1,-1),.7,colors.HexColor(BORDER)),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([t,Spacer(1,9)])
    n=d['included_tasks'];s=d['summary'];est=[e for e in d['analysis']['estimates'] if e['category']=='all']
    # 1 - Executive cover.
    para('INDIC HARNESS BENCH','white');para('What changed<br/>when instructions changed?','cover')
    para('An experimental report on English, Hindi and Hinglish<br/>OpenClaw + Ollama Cloud GPT-OSS-20B','white')
    story.append(Spacer(1,59))
    para('PARTIAL PHASE I  |  1 OCTOBER 2026','tag')
    table(['Matched tasks','Analyzed conditions','Tasks excluded for INFRA'],[[str(n),'138','8']],widths=[CW/3]*3)
    para('Higher Hindi scores, low full completion, and substantial uncertainty','h2')
    para(f'Hindi had the highest average deterministic score ({pct(s["hi"]["mean"])} / 100), followed by English ({pct(s["en"]["mean"])}), then Hinglish ({pct(s["hinglish"]["mean"])}). Full completion was rare: 5, 4 and 4 tasks respectively. Both overall paired score-difference intervals include zero.')
    callout('The proposed universal language-degradation pattern was not established. The experiment remains useful as a diagnosis of this specific model-harness configuration.')
    para('The analysis combines the first 40 tasks with the 14 added tasks, using the same settings. It retains only original tasks whose three primary language attempts are free of terminal infrastructure errors. The authorized task 037 retry does not restore that task to this report.')
    para('<b>Sample target:</b> 46 matched tasks is four below the requested minimum of 50. The 138 language conditions are not 138 independent research samples.','small')
    para('Compiled from the completed primary journal and saved oracle records. AI-written synthesis; no new model calls or benchmark runs were made to produce this report.','small')
    # 2 - Design.
    heading('01 / Design','A controlled instruction-language comparison')
    para('The question is whether changing the user instructions from English to Hindi or Hinglish changes executable agent performance, while holding the model, harness, task fixtures and scoring contract fixed. This is an exploratory configuration-level study, not a general test of Indian-language intelligence.')
    table(['Component','Recorded configuration'],[
      ['Model / service','gpt-oss:20b through Ollama Cloud; one model throughout'],['Harness','OpenClaw 2026.9.7; one serial attempt per language'],
      ['Generation','Temperature 0; medium reasoning effort; no model fallback'],['Context / response','OpenClaw contextWindow 65,536; response limit 4,096 tokens. Provider capacity was not independently verified.'],
      ['Per-attempt budgets','200,000 cumulative conservative input allowance; 16,000 output tokens; 30 physical inference requests'],
      ['Time / transport','min(source timeout, 600 seconds), shared across rounds; 120-second upstream transport wait; at most two transient transport retries'],
      ['Environment','2 CPUs, 3 GiB RAM, 256 PIDs, 512 MiB tmpfs workspace; Docker isolation'],
      ['Grade','Original deterministic oracle score, 0 to 1; integrity checks separate; no paid LLM judge']],[121,CW-121],small=True)
    para('What changes - and what stays English','h2')
    para('Every user instruction turn was translated. Hindi uses Devanagari with familiar technical terms; Hinglish uses Roman-script code switching. Paths, commands, identifiers, JSON keys, enum values, dates and exact strings stay literal. Fixtures, code, tool schemas, much of the harness context and required prose deliverables remain English. This tests an Indic-instruction / English-execution workflow.')
    para('State is reset between language attempts and preserved between rounds within an attempt. Language order rotates by original task index. All eight source families are represented. Translation and semantic checking were AI work, not independent bilingual human validation.','small')
    # 3 - Coverage / exclusions.
    heading('02 / Analysis population','From 54 scheduled tasks to 46 clean triplets')
    table(['Stage','Count','Interpretation'],[['Source definitions audited','106','Original reference suite'],['Curated and attempted','54 tasks / 162 conditions','40 initial tasks + 14 offline additions'],['Terminal infrastructure outcomes','10 conditions in 8 tasks','Each affected task is removed as a whole'],['Analyzed population','46 tasks / 138 conditions','36 initial + 10 added; 52 instruction turns']],[172,110,CW-282],small=True)
    para('Strict filter applied to all performance figures','h2')
    para('Remove a task if any of its three <b>primary</b> attempts has status <b>infrastructure_failed</b>. Do not substitute the task 037 retry, average across retries, or retain the unaffected language scores of an excluded task. Budget exhaustion remains a scored agent outcome. A recovered intermediate HTTP error alone is not a terminal INFRA outcome.')
    excluded_rows=[]
    for e in sorted(d['excluded_tasks'],key=lambda e:e['task_id']):
        excluded_rows.append([e['task_id'],', '.join(LABEL[l] for l in e['failed_languages']),e['cause']])
    table(['Excluded task','INFRA language(s)','Recorded cause'],excluded_rows,[212,88,CW-300],small=True)
    caption('Excluded scores do not enter any performance mean, interval, category chart or score atlas. This table is an accounting ledger, not performance evidence. Infrastructure events were observed in English, Hindi and Hinglish: 4, 4 and 2 respectively.')
    callout('54 scheduled tasks does not imply 54 valid samples. Under the requested rule, n = 46; reaching 50 requires at least four additional clean matched triplets.')
    # 4 - Results.
    heading('03 / Main results','Hindi leads on partial credit; full completion is scarce')
    image('overall');caption('Mean-score bars: 95% task-resampled percentile intervals, 10,000 resamples. Completion bars: descriptive 95% Wilson intervals. Each language has the same 46 original tasks; individual-language intervals are not a paired significance test.')
    table(['Language','Mean / 100','Median / 100','Full completion','Zero score','Budget stop'],[
        [LABEL[l],pct(s[l]['mean']),pct(s[l]['median']),f'{s[l]["full"]}/46 ({100*s[l]["full_rate"]:.1f}%)',str(s[l]['zero']),str(s[l]['budget'])] for l in LANGS],
        [77,78,81,113,74,CW-423],small=True)
    para('<b>Full completion</b> requires status completed, oracle score at least 0.9999, every exposed oracle check passing, and no integrity violation. A process marked completed can still score zero. A native oracle can also expose passing checks while assigning a fractional continuous score; the strict score-one rule is retained.')
    para('The configuration earned useful partial credit but did not reliably finish these workflows. Across the 138 analyzed conditions, only 13 fully completed, and 21 scored zero. A low completion ceiling limits how much a small language effect can be inferred from binary success alone.')
    # 5 - Paired results.
    heading('04 / Matched inference','The average language effects remain uncertain')
    image('paired_intervals');caption('Positive English-minus-Indic values favor English; negative values favor the Indic condition. Lines are paired task-resampled 95% percentile intervals; zero is the no-difference reference.')
    table(['Paired contrast','Score difference / pp','95% interval / pp','Completion difference / pp'],[
      ['English minus Hindi',f'{est[0]["score_difference_pp"]:+.2f}',f'[{est[0]["score_bootstrap_95_percent_interval_pp"][0]:+.2f}, {est[0]["score_bootstrap_95_percent_interval_pp"][1]:+.2f}]','+2.17'],
      ['English minus Hinglish',f'{est[1]["score_difference_pp"]:+.2f}',f'[{est[1]["score_bootstrap_95_percent_interval_pp"][0]:+.2f}, {est[1]["score_bootstrap_95_percent_interval_pp"][1]:+.2f}]','+2.17']],[157,97,117,CW-371],small=True)
    image('paired_scatter',height=229)
    caption('Each point is a matched original task; coincident points are combined and marker area grows with multiplicity. Above the diagonal, the Indic score is higher. The same task pair is the unit of comparison, not two independent groups.')
    para('Both overall score intervals cross zero. Both full-completion difference intervals are [-4.35, +10.87] percentage points. These observations neither establish universal degradation nor prove Hindi superiority or language equivalence.','small')
    # 6 - Categories.
    heading('05 / Categories','Language patterns vary across task families')
    image('categories',height=269)
    table(['Family','n','English','Hindi','Hinglish'],[[CAT_SHORT[c],str(d['categories'][c]['n'])]+[pct(d['categories'][c]['mean_scores'][l]) for l in LANGS] for c,_,_ in CATS],[230,30,80,80,CW-420],small=True)
    para('Hindi has higher observed means in professional workflows and communication; English has higher means in data/finance. Hinglish gains in evidence tasks but falls behind in several software and state tasks. Each family has only 4-7 observations. Category estimates are exploratory, with no correction for multiple comparisons.','small')
    para('Overall means weight every original task equally. They are not an equal-weight average of category means. Family names are shortened in the chart; the source taxonomy includes a multimodal label even though image tasks were excluded.','small')
    # 7 - Heterogeneity / cohort.
    heading('06 / Heterogeneity','Averages hide different execution paths')
    image('wins');caption('Higher / tied / lower compares each Indic score with English on the same task. Ties use a numerical tolerance of 0.000001; results are descriptive, not independent repeated trials.')
    para('A few large task gaps can move the average. Hindi was higher than English on 16 tasks and lower on 13, with 17 ties. Hinglish was higher on 8 and lower on 14, with 24 ties. The largest visible gains often coincide with producing required artifacts that another language condition omitted.')
    table(['Task example','English','Hindi','Hinglish','Observable contrast'],[
      ['005 Email triage','0.000','0.875','0.000','Hindi produced labels and most replies; other conditions lacked required IDs and reply artifacts.'],
      ['063 Alert deduplication','0.060','1.000','1.000','English missed incidents and noise-report files; both Indic conditions passed.'],
      ['034 Evidence matrix','0.000','0.000','0.840','Only Hinglish supplied the scored evidence-matrix artifact.'],
      ['035 Conflicting sources','0.690','0.000','0.659','Hindi lacked the facts and supporting outputs; English/Hinglish earned partial credit.']],[128,48,48,53,CW-277],small=True)
    para('Initial and extension cohorts','h2')
    table(['Cohort','Clean / scheduled','English mean','Hindi mean','Hinglish mean'],[[name,f'{co["retained"]}/{co["scheduled"]}']+[pct(co['mean_scores'][l]) for l in LANGS] for name,co in d['cohorts'].items()],[97,111,98,98,CW-404],small=True)
    caption('The added tasks were selected after the initial campaign and before their own model outcomes. Cohort means describe different task sets; higher extension scores do not show that the model improved over time. The combined analysis uses all 46 eligible tasks.')
    # 8 - Runtime / budgets.
    heading('07 / Operational performance','Budget stops are part of the measured behavior')
    image('resources');caption('Durations include controller preparation, model/tool activity and grading up to the recorded elapsed timestamp. Box plots summarize 46 attempts per language; workload and provider latency are not controlled timing benchmarks.')
    table(['Language','Median seconds','Requests','Recorded tool calls','Budget outcomes'],[[LABEL[l],f'{s[l]["median_sec"]:.1f}',str(s[l]['requests']),str(s[l]['tool_calls']),f'{s[l]["budget"]}/46'] for l in LANGS],[87,111,80,126,CW-404],small=True)
    triggers=collections.Counter(x['trigger'] for x in d['budget_events'])
    para(f'Of the 17 budget-exhausted analyzed conditions, {triggers["Input preflight allowance"]} stopped on input preflight and {triggers["Output allowance"]} on output allowance. They remain in the analysis with their original oracle scores; removing them would change the question and favor successful runs.')
    para('The controller reserves a conservative UTF-8 byte bound plus framing allowance before a request, then reconciles known provider usage. A next-request bound can exceed the remaining allowance even when known tokens are below 200,000. Uncertain transmissions keep their reservation charged. Consequently, the same numerical budget does not guarantee the same realized number of model steps.')
    caption('At most 30 physical upstream requests are allowed per attempt, including transport retries. Whole-attempt budgets span every round. Repeated short tool activity and longer contexts can spend the cumulative input allowance without approaching the 65,536-token context limit in a single call.')
    # 9 - Tokens / prompts.
    heading('08 / Context and usage','Prompt size is measurable; tokenizer causality is not')
    image('tokens');caption('Known provider-accounted tokens only, from the 138 analyzed conditions. Fourteen conditions have uncertain aggregate usage. These totals are lower bounds, not invoice or dollar-cost estimates.')
    table(['Language','Known input','Known output','Uncertain usage / 46','Transport retries'],[[LABEL[l],f'{s[l]["known_input"]:,}',f'{s[l]["known_output"]:,}',str(s[l]['uncertain_usage']),str(s[l]['transport_retries'])] for l in LANGS],[75,111,111,126,CW-423],small=True)
    table(['Indic / English ratio','Hindi','Hinglish'],[
       ['Mean full-instruction UTF-8 bytes',f'{d["prompt_ratios"]["hi"]["mean_prompt_byte_ratio"]:.3f}x',f'{d["prompt_ratios"]["hinglish"]["mean_prompt_byte_ratio"]:.3f}x'],
       ['Mean full-instruction characters',f'{d["prompt_ratios"]["hi"]["mean_prompt_character_ratio"]:.3f}x',f'{d["prompt_ratios"]["hinglish"]["mean_prompt_character_ratio"]:.3f}x'],
       ['Mean first-context provider input tokens',f'{d["prompt_ratios"]["hi"]["mean_first_context_token_ratio"]:.3f}x',f'{d["prompt_ratios"]["hinglish"]["mean_first_context_token_ratio"]:.3f}x']],[310,(CW-310)/2,(CW-310)/2],small=True)
    para('Ratios are paired by original task and averaged across 46 tasks. Instruction bytes/characters concatenate all prompt turns. First-context input tokens include the English system prompt, tool schemas and harness framing; isolated user-prompt token counts were not measured. Hindi used more UTF-8 bytes while first-context token inflation was about 1%, which cannot be treated as a causal tokenizer-tax estimate.','small')
    para('Four credential slots were configured, but the primary forwarding records show all 1,776 transmissions used anonymous slot-1. No paid credit purchases were made by the runner. Account quota availability and monetary cost were not established as measured outcomes.','small')
    # 10 - Failures.
    heading('09 / Failure diagnosis','Missing deliverables matter more than plausible narration')
    missing=d['symptoms']['missing_artifact_conditions']
    table(['Observed signal in analyzed runs','Count','How to interpret it'],[
      ['Explicit missing-artifact validator signal',str(missing)+' / 138','At least one failed check names a missing file or reports FileNotFound; signals may overlap.'],
      ['Zero oracle score','21 / 138','No scored credit; not automatically an infrastructure problem.'],
      ['Budget exhaustion','17 / 138','An attempted workflow stopped under the fixed compute guard.'],
      ['Strict full completion','13 / 138','All exposed checks, score-one threshold and integrity condition met.'],
      ['Observed integrity violations','0 / 138','No violation recorded; not proof of immunity to every attack.']],[208,78,CW-286],small=True)
    para('Evidence-grounded examples','h2')
    para('<b>Email merge (028):</b> Hindi scored 0.7273 but still failed thread-count, final-todo and required-fact checks. English hit its budget and Hinglish completed with 0.0909; both missed summary/reply evidence. Status completed is therefore a process state, not a quality guarantee.')
    para('<b>Kubernetes audit (062):</b> English scored 0.8699 while Hindi and Hinglish scored 0.14 and lacked the main audit CSV. All exposed English checks passed despite a fractional score, illustrating why this report preserves the continuous oracle and a separate strict full-completion flag.')
    para('<b>Evidence matrix (034):</b> Hinglish scored 0.84 but its evidence-phrase check reported only one of five decisive signals. This is a concrete partial semantic defect that an artifact-existence-only judge would miss.')
    callout('Observable files and validator checks support these diagnoses. They do not establish whether a failure originated in model understanding, tool use, context management or a hidden harness interaction.')
    caption('No paid LLM judge or independent human output judge was used. Tool-error counts, tool-schema-error counts, compaction-event counts and isolated user-prompt tokens remain unavailable. Some source oracles use lexical coverage and acceptance thresholds, so semantic validity may be weaker than the numeric score suggests.')
    # 11 - Engineering.
    heading('10 / Engineering record','What went wrong, and what was made safer')
    table(['Issue encountered','Response and study treatment'],[
      ['Early 100,000-input pilot stopped too soon','Archived and discarded from this analysis. A fresh 200,000-input campaign was run; none of the discarded pilot scores are pooled here.'],
      ['Local settlement acknowledgment failure','Idempotent accounting retries and persistent transmission receipts were checked; original failed record retained.'],
      ['Provider HTTP 500s and transport ambiguity','At most two transient retries, conservative reservation retention, durable failure saving, cooldown/continuation and outage pause. Terminal failures excluded as whole tasks.'],
      ['Successful response / broken pipe in 037 Hindi','One operator-authorized retry completed with score 0. Both records retained; task excluded from this report because its primary condition had INFRA.'],
      ['Reference oracle / fixture problems','Task 025 was replaced before observed outcomes; original oracle unchanged. Private fixture layout/LF adaptations were documented and validated.'],
      ['Translation contract drift','Natural-language revision, literal checks, shared output clarifications and final AI semantic checks before freeze. Not independent human review.']],[151,CW-151],small=True)
    para('Safety and preservation','h2')
    para('The entire OpenClaw process runs in Docker, as a non-root user with a read-only root, dropped capabilities, no-new-privileges, seccomp and bounded resources. Agent containers receive no Windows bind mounts, host drives, Docker control interfaces or cloud credentials. A restricted relay owns inference credentials; graders have no network or credentials and run after the agent stops.')
    para('SQLite transactions commit before inference forwarding. Round checkpoints, bounded traces and safe exports stay outside agent storage. Cleanup targets only recorded owned resources. The extended grader passed compatibility checks for the original 40 tasks; all 120 original records remain preserved. Before the extension, 50 controller tests and fresh integration checks passed with fake inference.','small')
    caption('Tests included Hindi text roundtrips, multi-round state, quota handling, lost acknowledgments, blocked host access and save/reopen. Tests reduce known risks; Docker isolation and local backups do not guarantee protection against kernel vulnerabilities or physical disk loss.')
    # 12 - Interpretation.
    heading('11 / Interpretation','What this experiment supports - and what it cannot')
    para('Findings supported by these records','h2')
    para('1. The particular GPT-OSS-20B / OpenClaw configuration frequently earns partial credit and rarely finishes all task requirements. This weak absolute baseline is itself an actionable finding.<br/>2. Language effects are heterogeneous. Hindi has a higher observed overall mean, while Hinglish has a lower one; neither overall paired score interval excludes zero.<br/>3. Required-artifact omissions, budget preflight and provider availability are material operational limitations. Scoring only natural-language answers would hide many of these failures.')
    para('Boundaries on interpretation','h2')
    para('Only one model, one harness and one primary attempt per language were measured. Temperature zero does not establish deterministic cloud execution. Tasks were feasibility-curated, translations and oracle validation were AI-reviewed, and the added tasks were selected after the initial campaign. Fixtures and outputs remain English. Category samples are small and unequal, the complete-case filter can select a nonrepresentative subset, and runtime implementation revisions span the campaign.')
    para('A confidence interval spanning zero is not proof of equivalence. A higher mean on this curated sample is not a broad claim about Hindi capability. The report cannot isolate tokenizer effects, assign hidden cognitive responsibility to the model versus harness, or support general claims for Indian languages beyond these Hindi/Hinglish instruction variants.')
    para('Next steps for a more credible paper','h2')
    para('1. Add at least four validated clean triplets if 50 analyzable tasks is mandatory; allow a buffer for infrastructure loss, and lock selection before new outcomes.<br/>2. Obtain bilingual human prompt review and targeted output review, while keeping original deterministic scores available.<br/>3. Pre-specify repeated matched attempts and counterbalanced scheduling; report within-task variability and multiple-comparison caution.<br/>4. Run a separate stronger-model or harness comparison under a frozen uniform protocol; do not pool it silently with this configuration.<br/>5. Measure isolated prompt tokens, actual context growth, tool-schema failures and compaction events before claiming causal tokenizer or harness effects.')
    callout('The research hypothesis is a question to test, not a result to force. An unexpected direction with honest uncertainty and operational evidence is a valid exploratory study outcome.')
    # 13/14 - Every included task.
    for page in [1,2]:
        heading(f'Appendix A / score atlas {page} of 2','Every included task, every language')
        para('Original deterministic scores, range 0-1. Cells marked * are budget-exhausted outcomes and remain in the analysis. No INFRA-affected task or recovered replacement appears in this atlas.','small')
        image('task_atlas_'+str(page),height=550)
        caption('Task IDs match the preserved source suite. For exact raw precision, status and usage, see the PDF attachment included_condition_metrics.csv or the report_data folder. Colors encode score only; they are not a separate quality judgment.')
    # 15 - Reproducibility / sources.
    heading('Appendix B / audit trail','Reproduce the analysis from the saved evidence')
    para('Analysis definitions','h2')
    para('Mean score = arithmetic mean of original oracle scores across the same 46 tasks. Contrast = 100 x mean(score_English - score_Indic). Completion contrast uses strict full-completion flags. Paired percentile intervals resample original tasks with replacement, keeping language conditions together: 10,000 resamples, seed 20260930. No task weighting by number of checks, rounds or tool calls is used.')
    table(['Evidence / provenance','Value'],[
      ['Campaign dates (India time)',d['primary_start_ist'][:19].replace('T',' ')+' to '+d['primary_end_ist'][:19].replace('T',' ')],
      ['Study ID',d['freeze']['study_id']],['Final runtime freeze',d['freeze']['dataset_hash']],
      ['Primary run-record SHA-256',d['primary_run_records_sha256']],
      ['Preserved references','1,116 hashed files; reference and vendor unchanged at report generation'],
      ['Included runtime hash prefixes',', '.join(k[:12]+' ('+str(v)+' runs)' for k,v in d['runtime_counts'].items())]],[143,CW-143],small=True)
    para('The fresh 200,000-input study is the sole results source. Earlier discarded-pilot scores and older Indic-attempt results are not used. The initial 40-record preservation snapshot and the extension freeze document append-only provenance. Runtime versions changed infrastructure behavior; they do not justify a causal separation of model and harness effects.','small')
    para('Sources','h2')
    para('[1] Yao, Y.; Tan, X.; Liu, C.-H.; et al. (2026). <i>Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows.</i> arXiv:2605.27922v1, 27 May 2026. Supplied reference PDF and source snapshot. <link href="https://arxiv.org/abs/2605.27922" color="#325EA8">arxiv.org/abs/2605.27922</link><br/>[2] <i>Indic_Harness_Bench_Proposal.pdf.</i> Supplied project proposal; the present work covers a narrowed instruction-translation Phase I.<br/>[3] Primary evidence: results/journal.sqlite3, results/runs/, config/protocol.json, dataset/task_manifest.json, dataset/freeze.json.<br/>[4] Validation and methods: reports/additional14_methods.md, reports/oracle_validation.json, reports/extension_original_oracle_compatibility.json, reports/*_check.json, reports/FRESH_RUN.md and reports/accounting_retry_repair.json.','small')
    para('Companion evidence','h2')
    para('pdf/report_data contains analysis_summary.json, included_condition_metrics.csv, excluded_task_ledger.csv and a filtered task-score table. The PDF embeds the included CSV and excluded ledger. pdf/figures contains PNG and vector SVG charts. scripts/build_experiment_report.py rebuilds this report without model calls. No credentials, private validation solutions or full ground-truth fixtures are included.','small')
    def decorate(canvas,doc):
        page=doc.page
        if page==1:
            canvas.setFillColor(colors.HexColor(INK));canvas.rect(0,H-253,W,253,fill=1,stroke=0)
        else:
            canvas.setStrokeColor(colors.HexColor(BORDER));canvas.line(46,H-39,W-46,H-39)
            canvas.setFont('SegoeBold',8);canvas.setFillColor(colors.HexColor(INK));canvas.drawString(46,H-29,'INDIC HARNESS BENCH')
            canvas.setFont('Segoe',8);canvas.setFillColor(colors.HexColor(MUTED));canvas.drawRightString(W-46,H-29,'EXPERIMENT REPORT  |  01 OCT 2026')
        canvas.setStrokeColor(colors.HexColor(BORDER));canvas.line(46,40,W-46,40)
        canvas.setFillColor(colors.HexColor(MUTED));canvas.setFont('Segoe',7.5);canvas.drawString(46,27,'46 matched tasks / 138 conditions  |  Strict INFRA-free primary analysis')
        canvas.drawRightString(W-46,27,f'{page:02d}')
    base=TMP/'report-base.pdf'
    doc=SimpleDocTemplate(str(base),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=62,bottomMargin=53,
        title='Indic Harness Bench: Experiment Report',author='Indic Harness Bench project',subject='Strict infrastructure-free matched analysis of English, Hindi and Hinglish tasks')
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    writer=PdfWriter();writer.clone_document_from_reader(PdfReader(base))
    for filename in ('included_condition_metrics.csv','excluded_task_ledger.csv'):
        writer.add_attachment(filename,(DATA/filename).read_bytes())
    headings=['Executive findings','Study design','Coverage and exclusion rule','Overall outcomes','Paired language differences','Category results','Task heterogeneity','Budget and runtime','Context and token usage','Failure diagnosis','Engineering and security','Interpretation and next steps','Task score atlas A','Task score atlas B','Reproducibility and sources']
    if len(writer.pages)==len(headings):
        for i,title in enumerate(headings):writer.add_outline_item(title,i)
    writer.add_metadata({'/Title':'Indic Harness Bench - Experiment Report','/Author':'Indic Harness Bench project','/Subject':'46 matched infrastructure-free tasks; GPT-OSS-20B / OpenClaw; instruction-language comparison'})
    target=OUT/'Indic_Harness_Bench_Experiment_Report.pdf'
    with target.open('wb') as stream:writer.write(stream)
    return target


def main():
    for directory in (OUT,DATA,FIG,TMP):directory.mkdir(parents=True,exist_ok=True)
    d,g,meta=collect()
    dump(DATA/'analysis_summary.json',d)
    metrics=d['included_metrics'];fields=list(metrics[0])
    with (DATA/'included_condition_metrics.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for m in metrics:writer.writerow({k:encode(v) if isinstance(v,(list,dict)) else v for k,v in m.items()})
    with (DATA/'excluded_task_ledger.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['task_id','category','failed_languages','cause']);writer.writeheader()
        for r in d['excluded_tasks']:writer.writerow({k:', '.join(r[k]) if k=='failed_languages' else r[k] for k in writer.fieldnames})
    with (DATA/'included_task_scores.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['task_id','category','english','hindi','hinglish','english_status','hindi_status','hinglish_status'])
        for task,v in sorted(g.items()):writer.writerow([task,meta[task]['category']]+[v[l]['original_score'] for l in LANGS]+[v[l]['status'] for l in LANGS])
    figures=plots(d,g);target=report(d,g,meta,figures)
    reader=PdfReader(target)
    print(json.dumps({'pdf':str(target),'pages':len(reader.pages),'included_tasks':d['included_tasks'],'included_conditions':d['included_conditions'],'excluded_tasks':len(d['excluded_tasks']),'figures':len(figures),'primary_results_modified':False},indent=2))


if __name__=='__main__':main()
