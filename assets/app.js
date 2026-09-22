"use strict";

// Sample assignment data
const courses=[
  {code:'CS 0445',name:'Data Structures',section:'LEC 01',type:'Lecture',enrollment:118,hours:30,priority:'High',tas:['ML','AK'],match:94,status:'Staffed'},
  {code:'CS 0445',name:'Data Structures',section:'LAB 02',type:'Laboratory',enrollment:32,hours:10,priority:'High',tas:['PR'],match:91,status:'Staffed'},
  {code:'CS 0445',name:'Data Structures',section:'LAB 03',type:'Laboratory',enrollment:29,hours:10,priority:'High',tas:[],match:68,status:'Needs TA'},
  {code:'CS 1501',name:'Algorithm Implementation',section:'LEC 01',type:'Lecture',enrollment:86,hours:20,priority:'High',tas:['JL','SK'],match:89,status:'Staffed'},
  {code:'CS 1675',name:'Intro to Machine Learning',section:'LEC 01',type:'Lecture',enrollment:74,hours:20,priority:'High',tas:['RN','DC'],match:96,status:'Staffed'},
  {code:'CS 1550',name:'Operating Systems',section:'REC 01',type:'Recitation',enrollment:38,hours:10,priority:'Normal',tas:['EW'],match:82,status:'Staffed'},
  {code:'CS 1656',name:'Database Management',section:'LEC 01',type:'Lecture',enrollment:64,hours:20,priority:'Normal',tas:['NO'],match:85,status:'Staffed'},
  {code:'CS 1520',name:'Web Applications',section:'LAB 01',type:'Laboratory',enrollment:34,hours:10,priority:'Normal',tas:['IH'],match:88,status:'Staffed'}
];
const tas=[
  {name:'Maya Liu',initials:'ML',hours:'18 / 15 preferred',skills:'CS 0445 · CS 1501',constraint:'Tue after 4 PM',ready:'Review'},
  {name:'Alex Kim',initials:'AK',hours:'15 / 20 hours',skills:'CS 0445 · CS 1520',constraint:'None',ready:'Ready'},
  {name:'Jordan Lee',initials:'JL',hours:'20 / 20 hours',skills:'CS 1501 · CS 1675',constraint:'No Friday',ready:'Ready'},
  {name:'Priya Rao',initials:'PR',hours:'10 / 20 hours',skills:'CS 0445 · CS 1656',constraint:'Mon/Wed only',ready:'Ready'},
  {name:'Samir Khan',initials:'SK',hours:'15 / 20 hours',skills:'Algorithms · ML',constraint:'After 11 AM',ready:'Ready'},
  {name:'Rina Nair',initials:'RN',hours:'20 / 20 hours',skills:'ML · Data Science',constraint:'None',ready:'Ready'},
  {name:'Diego Cruz',initials:'DC',hours:'10 / 15 hours',skills:'ML · Databases',constraint:'No mornings',ready:'Ready'}
];
const assignments=[
  ['CS 0445 · LEC 01','Maya Liu + Alex Kim','30','94%','Unchanged'],['CS 0445 · LAB 02','Priya Rao','10','91%','Unchanged'],['CS 0445 · LAB 03','Unassigned','10','68%','Needs decision'],['CS 1501 · LEC 01','Jordan Lee + Samir Khan','35','89%','Unchanged'],['CS 1675 · LEC 01','Rina Nair + Diego Cruz','30','96%','Unchanged'],['CS 1550 · REC 01','Erin Wu','10','82%','Moved from LAB 02'],['CS 1656 · LEC 01','Noah Ortiz','20','85%','Unchanged'],['CS 1520 · LAB 01','Imani Hall','10','88%','Unchanged']
];
const initialsClass=(i)=>i==='PR'||i==='RN'?' a2':i==='JL'||i==='SK'?' a3':'';
// Rendering helpers
function renderProposal(){document.getElementById('proposalBody').innerHTML=courses.slice(0,5).map(c=>`<tr><td><div class="course"><span class="course-code">${c.code.replace('CS ','')}</span><div><strong>${c.code} · ${c.section}</strong><span>${c.name}</span></div></div></td><td>${c.enrollment}</td><td><div class="avatar-stack">${c.tas.length?c.tas.map(i=>`<span class="avatar${initialsClass(i)}" title="${i}">${i}</span>`).join(''):'<span style="color:#a33b49">Unassigned</span>'}</div></td><td><div class="score ${c.match<75?'low':''}"><span class="bar"><i style="width:${c.match}%"></i></span><strong>${c.match}%</strong></div></td><td><span class="pill ${c.status==='Staffed'?'good':'bad'}">${c.status}</span></td></tr>`).join('')}
function renderCourses(query=''){const list=courses.filter(c=>(c.code+c.name+c.section).toLowerCase().includes(query.toLowerCase()));document.getElementById('courseBody').innerHTML=list.map(c=>`<tr><td><div class="course"><span class="course-code">${c.code.replace('CS ','')}</span><div><strong>${c.code} · ${c.section}</strong><span>${c.name}</span></div></div></td><td>${c.type}</td><td>${c.enrollment}</td><td>${c.hours} hrs/week</td><td><span class="pill ${c.priority==='High'?'warn':'good'}">${c.priority}</span></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No courses match that search.</td></tr>'}
function renderTAs(query=''){const list=tas.filter(t=>(t.name+t.skills).toLowerCase().includes(query.toLowerCase()));document.getElementById('taBody').innerHTML=list.map(t=>`<tr><td><div class="person"><span class="avatar">${t.initials}</span><div><strong>${t.name}</strong><span>Graduate TA</span></div></div></td><td>${t.hours}</td><td>${t.skills}</td><td>${t.constraint}</td><td><span class="pill ${t.ready==='Ready'?'good':'warn'}">${t.ready}</span></td></tr>`).join('')||'<tr><td colspan="5" class="empty">No teaching assistants match that search.</td></tr>'}
function renderAssignments(){document.getElementById('assignmentBody').innerHTML=assignments.map(a=>`<tr><td><strong>${a[0]}</strong></td><td>${a[1]}</td><td>${a[2]} hrs/week</td><td><span class="pill ${parseInt(a[3])>85?'good':'warn'}">${a[3]}</span></td><td>${a[4]}</td></tr>`).join('')}
renderProposal();renderCourses();renderTAs();renderAssignments();
// View navigation
const titles={overview:['Assignment overview','Spring 2027 planning workspace'],courses:['Courses','Demand and section requirements'],tas:['Teaching assistants','Availability, preferences, and constraints'],assignments:['Assignments','Review the complete proposed plan'],'scoring-test':['Scoring test','Run and inspect the preference model'],constraints:['Constraints','Rules and optimization priorities']};
function showView(id){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===id));document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===id));document.getElementById('viewTitle').textContent=titles[id][0];document.getElementById('viewSubtitle').textContent=titles[id][1];document.getElementById('sidebar').classList.remove('open');if(window.location.hash!==`#${id}`)history.replaceState(null,'',`#${id}`);window.scrollTo({top:0,behavior:'smooth'})}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.go)));
function toast(title,text){document.getElementById('toastTitle').textContent=title;document.getElementById('toastText').textContent=text;const el=document.getElementById('toast');el.classList.add('show');clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>el.classList.remove('show'),3200)}
// Coordinator actions
document.getElementById('runBtn').addEventListener('click',()=>{const b=document.getElementById('runBtn');b.disabled=true;b.textContent='Optimizing…';document.getElementById('runStatus').textContent='Run #05 in progress';setTimeout(()=>{b.disabled=false;b.innerHTML='<svg viewBox="0 0 24 24"><path d="M5 3l14 9-14 9z"/></svg>Run assignment';document.getElementById('runStatus').textContent='Run #05 complete';toast('New proposal ready','14 sections evaluated in 1.2 seconds. Two decisions still need review.')},1100)});
document.getElementById('exportBtn').addEventListener('click',()=>{const csv=['Course,Teaching assistant,Hours,Match,Change',...assignments.map(a=>a.map(v=>`"${v}"`).join(','))].join('\n');const blob=new Blob([csv],{type:'text/csv'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='spring-2027-ta-assignments.csv';a.click();URL.revokeObjectURL(url);toast('CSV exported','The current assignment draft was downloaded.')});
document.getElementById('courseSearch').addEventListener('input',e=>renderCourses(e.target.value));document.getElementById('taSearch').addEventListener('input',e=>renderTAs(e.target.value));
document.getElementById('addCourse').addEventListener('click',()=>toast('Course intake ready','A production version would open the course import form here.'));document.getElementById('addTA').addEventListener('click',()=>toast('TA intake ready','A production version would open the applicant import form here.'));
['students','hours','stability'].forEach(id=>{const input=document.getElementById(id+'Range'),out=document.getElementById(id+'Out');input.addEventListener('input',()=>{out.textContent=input.value+(id==='stability'?'%':'')})});
document.querySelectorAll('.switch').forEach(s=>s.addEventListener('click',()=>{s.classList.toggle('on');s.setAttribute('aria-checked',s.classList.contains('on'))}));
document.getElementById('simulateBtn').addEventListener('click',()=>{document.getElementById('changeResult').classList.add('show');document.getElementById('changeMetric').textContent='1';assignments[3][1]='Samir Khan + Casey Nguyen';assignments[3][4]='1 TA replaced';renderAssignments();document.getElementById('diffBanner').classList.add('show');toast('Late change simulated','The model preserved 12 placements and changed only one.')});
document.getElementById('dismissDiff').addEventListener('click',()=>document.getElementById('diffBanner').classList.remove('show'));
document.querySelectorAll('.resolveBtn').forEach(b=>b.addEventListener('click',()=>{showView('assignments');toast('Candidate options opened','The unstaffed lab is highlighted in the full plan.')}));
document.getElementById('menuBtn').addEventListener('click',()=>document.getElementById('sidebar').classList.toggle('open'));

// Real preference-scoring test UI
const testTopicWeight=document.getElementById('testTopicWeight');
const testPreferenceWeight=document.getElementById('testPreferenceWeight');
const testCourseSelect=document.getElementById('testCourseSelect');
const testPeopleSoftReport=document.getElementById('testPeopleSoftReport');
let scoringTestData=null;
const escapeHtml=(value)=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
function syncTestWeights(changed){if(changed==='topic')testPreferenceWeight.value=100-Number(testTopicWeight.value);else testTopicWeight.value=100-Number(testPreferenceWeight.value);document.getElementById('testTopicOut').textContent=testTopicWeight.value;document.getElementById('testPreferenceOut').textContent=testPreferenceWeight.value}
testTopicWeight.addEventListener('input',()=>syncTestWeights('topic'));
testPreferenceWeight.addEventListener('input',()=>syncTestWeights('preference'));
function renderTestRankings(){
  if(!scoringTestData)return;
  const course=testCourseSelect.value;
  const rows=scoringTestData.rankings.filter(row=>row.course===course);
  const eligibleCount=rows.filter(row=>row.eligible).length;
  document.getElementById('testResultCaption').textContent=`${eligibleCount} eligible of ${rows.length} candidates for ${course}.`;
  let eligibleRank=0;
  document.getElementById('testRankingBody').innerHTML=rows.map(row=>{
    const rank=row.eligible?++eligibleRank:'—';
    const reason=row.disqualifiers?.join('; ')||'Eligible';
    const score=row.overall_score==null?'—':row.overall_score.toFixed(1);
    const topic=row.topic_fit==null?'—':`${row.topic_fit.toFixed(1)}%`;
    return `<tr><td><strong>${rank}</strong></td><td><div class="person"><span class="avatar">${escapeHtml((row.name||'?').split(/\s+/).map(part=>part[0]).join('').slice(0,2).toUpperCase())}</span><div><strong>${escapeHtml(row.name||'Unnamed candidate')}</strong><span>${escapeHtml(row.email||'No email')}</span></div></div></td><td><strong>${score}</strong></td><td>${topic}</td><td>${escapeHtml(row.preference||'Missing')}</td><td><span class="pill ${row.eligible?'good':'bad'}" title="${escapeHtml(reason)}">${row.eligible?'Eligible':'Excluded'}</span></td></tr>`;
  }).join('')||'<tr><td colspan="6" class="empty">No candidates were returned for this course.</td></tr>';
}
function renderPeopleSoftSections(){
  const peoplesoft=scoringTestData?.peoplesoft;
  const body=document.getElementById('testSectionBody');
  if(!peoplesoft){
    document.getElementById('testSectionCaption').textContent='No readable PeopleSoft report was available for this run.';
    body.innerHTML='<tr><td colspan="7" class="empty">Add a generated .xlsx report to scripts/PeopleSoft Scraper/reports and run again.</td></tr>';
    return;
  }
  document.getElementById('testSectionCaption').textContent=`${peoplesoft.mapped_section_count} of ${peoplesoft.section_count} sections matched the current course map.`;
  body.innerHTML=peoplesoft.sections.map(section=>{
    const needs=[];
    if(section.recitation_ta_need!==null&&section.recitation_ta_need!=='')needs.push(`Recitation ${section.recitation_ta_need}`);
    if(section.grader_need!==null&&section.grader_need!=='')needs.push(`Grading ${section.grader_need}`);
    const score=section.top_score==null?'—':section.top_score.toFixed(1);
    return `<tr><td><div class="course"><span class="course-code">${escapeHtml(section.course_code.replace(/^\S+\s/,''))}</span><div><strong>${escapeHtml(section.course_code)}</strong><span>${escapeHtml(section.name||'Unnamed course')}</span></div></div></td><td>${escapeHtml(section.class_number||'—')}</td><td>${escapeHtml(section.component||'—')}</td><td>${section.enrollment??'—'}</td><td>${escapeHtml(needs.join(' · ')||'—')}</td><td>${escapeHtml(section.top_candidate||'Not mapped')}</td><td><strong>${score}</strong></td></tr>`;
  }).join('')||'<tr><td colspan="7" class="empty">The selected report contains no course sections.</td></tr>';
}
testCourseSelect.addEventListener('change',renderTestRankings);
document.getElementById('testRunBtn').addEventListener('click',async()=>{
  const button=document.getElementById('testRunBtn');
  const error=document.getElementById('testError');
  button.disabled=true;
  button.textContent='Running Python pipeline…';
  error.textContent='';
  document.getElementById('testRunStatus').textContent='Run in progress';
  try{
    const response=await fetch('/api/run-scoring',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic_weight:Number(testTopicWeight.value)/100,preference_weight:Number(testPreferenceWeight.value)/100,peoplesoft_report:testPeopleSoftReport.disabled?null:testPeopleSoftReport.value})});
    const payload=await response.json();
    if(!response.ok)throw new Error(payload.error||'The scoring run failed.');
    scoringTestData=payload;
    document.getElementById('testRunStatus').textContent=`Run #${payload.run_number} complete`;
    document.getElementById('testProfiles').textContent=payload.profile_count;
    document.getElementById('testCourses').textContent=payload.course_count;
    document.getElementById('testRankings').textContent=payload.ranking_count;
    document.getElementById('testTimestamp').textContent=`Completed ${new Date(payload.generated_at).toLocaleString()}`;
    document.getElementById('testOutput').textContent=payload.outputs.rankings;
    const previous=testCourseSelect.value;
    testCourseSelect.innerHTML=payload.courses.map(item=>`<option value="${escapeHtml(item.course)}">${escapeHtml(item.course)} · ${item.eligible_count} eligible</option>`).join('');
    testCourseSelect.disabled=false;
    if(payload.courses.some(item=>item.course===previous))testCourseSelect.value=previous;
    renderTestRankings();
    renderPeopleSoftSections();
    toast('Scoring test complete',`${payload.ranking_count} candidate-course rankings generated.`);
  }catch(runError){
    document.getElementById('testRunStatus').textContent='Run failed';
    error.textContent=runError.message==='Failed to fetch'?'Start the Python testing UI server, then reload this page.':runError.message;
  }finally{
    button.disabled=false;
    button.innerHTML='<svg viewBox="0 0 24 24"><path d="M5 3l14 9-14 9z"/></svg>Run scoring test';
  }
});
fetch('/api/scoring-config').then(response=>response.ok?response.json():Promise.reject()).then(config=>{
  document.getElementById('testWorkbook').textContent=config.workbook;
  document.getElementById('testCourseMap').textContent=config.course_map;
  if(config.peoplesoft_reports.length){
    testPeopleSoftReport.innerHTML=config.peoplesoft_reports.map(path=>`<option value="${escapeHtml(path)}">${escapeHtml(path.split(/[\\/]/).pop())}</option>`).join('');
    testPeopleSoftReport.disabled=false;
    document.getElementById('testPeopleSoftNote').textContent='Read-only test input. The workbook will not be modified.';
  }else{
    document.getElementById('testPeopleSoftNote').textContent=config.peoplesoft_warning;
  }
}).catch(()=>{});
const initialView=window.location.hash.slice(1);
if(titles[initialView])showView(initialView);
// Optional browser-agent integration
if(document.modelContext?.registerTool){const lifecycle=new AbortController();const register=(tool)=>Promise.resolve(document.modelContext.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});register({name:'read_assignment_summary',title:'Read assignment summary',description:'Read the current TA assignment coverage, fit score, assigned hours, and unresolved issue count.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:false},execute:()=>({term:'Spring 2027',coverage:{staffed:13,total:14},preferenceFit:87,assignedHours:186,availableHours:200,unresolvedIssues:2})});register({name:'run_assignment',title:'Run assignment',description:'Run the visible TA assignment optimizer using the current constraints and update the proposal.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute:async()=>{document.getElementById('runBtn').click();await new Promise(r=>setTimeout(r,1200));return{run:5,status:'complete',sectionsEvaluated:14,unresolvedIssues:2}}});register({name:'simulate_late_withdrawal',title:'Simulate late withdrawal',description:'Remove the sample TA Jordan Lee, replan the assignment, and show how many placements changed or stayed fixed.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute:()=>{showView('constraints');document.getElementById('simulateBtn').click();return{removed:'Jordan Lee',placementsChanged:1,placementsPreserved:12,coveragePercent:93}}})}
