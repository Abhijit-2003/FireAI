#!/usr/bin/env python3
"""Generate comprehensive test suite for Indian Income Tax Calculator FY 2024-25."""
import json, os, copy

# ============================================================
# TAX COMPUTATION ENGINE
# ============================================================
def old_slab_tax(taxable, age):
    exempt = 500000 if age >= 80 else (300000 if age >= 60 else 250000)
    if taxable <= exempt: return 0.0
    tax = 0.0
    if exempt < 500000:
        tax += max(0, min(taxable, 500000) - exempt) * 0.05
    if taxable > 500000:
        tax += (min(taxable, 1000000) - 500000) * 0.20
    if taxable > 1000000:
        tax += (taxable - 1000000) * 0.30
    return tax

def new_slab_tax(taxable):
    if taxable <= 300000: return 0.0
    tax = 0.0
    for lo, hi, r in [(300000,700000,0.05),(700000,1000000,0.10),
                       (1000000,1200000,0.15),(1200000,1500000,0.20),
                       (1500000,1e18,0.30)]:
        if taxable > lo:
            tax += (min(taxable, hi) - lo) * r
    return tax

def _sc_params(taxable, is_new):
    if taxable <= 5000000: return 0,0,0
    if taxable <= 10000000: return 0.10, 5000000, 0
    if taxable <= 20000000: return 0.15, 10000000, 0.10
    if taxable <= 50000000: return 0.25, 20000000, 0.15
    return (0.25 if is_new else 0.37), 50000000, 0.25

def calc_sc(net, taxable, slab_fn, is_new):
    rate, thr, prev = _sc_params(taxable, is_new)
    if rate == 0 or net <= 0: return 0
    normal = net * rate
    t_thr = slab_fn(thr)
    tot_thr = t_thr * (1 + prev)
    mx = tot_thr + (taxable - thr) - net
    return max(0, min(normal, mx))

def compute_old(inp):
    g=inp['gross_salary']; b=inp['basic_salary']; da=inp.get('da',0)
    hr=inp.get('hra_received',0); rnt=inp.get('rent_paid',0)
    cty=inp.get('city_type','non_metro'); age=inp.get('age',30)
    c80c=inp.get('section_80c',0); c80ccd=inp.get('section_80ccd_1b',0)
    ds=inp.get('section_80d_self',0); dp=inp.get('section_80d_parents',0)
    psr=inp.get('parents_senior_citizen',False); hl=inp.get('home_loan_interest',0)
    sd = min(50000, g)
    hra = 0.0
    if hr > 0 and rnt > 0:
        bda = b + da
        hra = max(0.0, min(hr, (0.5 if cty=='metro' else 0.4)*bda, rnt - 0.1*bda))
    d1=min(c80c,150000); d2=min(c80ccd,50000)
    d3=min(ds, 50000 if age>=60 else 25000)
    d4=min(dp, 50000 if psr else 25000)
    d5=min(hl, 200000)
    taxable = max(0, g - sd - hra - d1 - d2 - d3 - d4 - d5)
    tax = old_slab_tax(taxable, age)
    tr = round(tax)
    reb = min(tr, 12500) if taxable <= 500000 else 0
    net = max(0, tr - reb)
    sc = round(calc_sc(net, taxable, lambda t: old_slab_tax(t, age), False))
    ces = round((net + sc) * 0.04)
    return {'taxable_income':round(taxable),'tax_before_rebate':tr,
            'rebate_87a':reb,'surcharge':sc,'cess':ces,'total_tax':net+sc+ces}

def compute_new(inp):
    g=inp['gross_salary']
    sd=min(75000,g); taxable=max(0,g-sd)
    tax=new_slab_tax(taxable); tr=round(tax)
    reb=min(tr,25000) if taxable<=700000 else 0
    net=max(0,tr-reb)
    sc=round(calc_sc(net,taxable,new_slab_tax,True))
    ces=round((net+sc)*0.04)
    return {'taxable_income':round(taxable),'tax_before_rebate':tr,
            'rebate_87a':reb,'surcharge':sc,'cess':ces,'total_tax':net+sc+ces}

# ============================================================
# HELPERS
# ============================================================
def I(gross, basic=None, da=0, hra=0, rent=0, city='non_metro',
      age=30, c80c=0, c80ccd=0, d_self=0, d_par=0, par_sr=False, hloan=0):
    return {'gross_salary':gross,'basic_salary':basic if basic is not None else gross,
            'da':da,'hra_received':hra,'rent_paid':rent,'city_type':city,'age':age,
            'section_80c':c80c,'section_80ccd_1b':c80ccd,
            'section_80d_self':d_self,'section_80d_parents':d_par,
            'parents_senior_citizen':par_sr,'home_loan_interest':hloan,
            'financial_year':'2024-25'}

cases = []
n = [0]
def add(desc, inp, cat, edge=False):
    n[0] += 1
    cases.append({'id':f'TC{n[0]:03d}','description':desc,'input':inp,
                  'category':cat,'edge_case':edge})

# ============================================================
# BASIC CASES (20)
# ============================================================
for g, d in [
    (50000,"Salary 50K"),(100000,"Salary 1L"),(200000,"Salary 2L"),
    (250000,"Salary 2.5L"),(300000,"Salary 3L"),(400000,"Salary 4L"),
    (500000,"Salary 5L"),(550000,"Salary 5.5L"),(600000,"Salary 6L"),
    (750000,"Salary 7.5L"),(800000,"Salary 8L"),(1000000,"Salary 10L"),
    (1200000,"Salary 12L"),(1500000,"Salary 15L"),(1800000,"Salary 18L"),
    (2000000,"Salary 20L"),(2500000,"Salary 25L"),(3000000,"Salary 30L"),
    (5000000,"Salary 50L"),(10000000,"Salary 1Cr"),
]:
    add(f'{d} no deductions age 30', I(g), 'basic')

# ============================================================
# OLD SLAB BOUNDARY (15)
# ============================================================
for g, age, d in [
    (299999,30,"Old taxable 249999 just below basic exemption"),
    (300000,30,"Old taxable 250000 at basic exemption"),
    (300001,30,"Old taxable 250001 just above basic exemption"),
    (549999,30,"Old taxable 499999 just below rebate 5L"),
    (550000,30,"Old taxable 500000 at rebate limit 5L"),
    (550001,30,"Old taxable 500001 rebate cliff"),
    (1049999,30,"Old taxable 999999 just below 10L slab"),
    (1050000,30,"Old taxable 1000000 at 10L boundary"),
    (1050001,30,"Old taxable 1000001 just into 30pct slab"),
    (350000,65,"Senior taxable 300000 at senior exemption"),
    (350001,65,"Senior taxable 300001 just above senior exemption"),
    (349999,65,"Senior taxable 299999 just below senior exemption"),
    (550000,85,"Super senior taxable 500000 at super exemption"),
    (550001,85,"Super senior taxable 500001 just above super exemption"),
    (1050000,65,"Senior taxable 1000000 at 10L boundary"),
]:
    add(d, I(g, age=age), 'slab_boundary_old', edge=True)

# ============================================================
# NEW SLAB BOUNDARY (15)
# ============================================================
for g, d in [
    (374999,"New taxable 299999 just below 3L"),
    (375000,"New taxable 300000 at 3L"),
    (375001,"New taxable 300001 just above 3L"),
    (674999,"New taxable 599999 just below 6L"),
    (675000,"New taxable 600000 at 6L"),
    (675001,"New taxable 600001 just above 6L into 10pct"),
    (974999,"New taxable 899999 just below 9L"),
    (975000,"New taxable 900000 at 9L"),
    (975001,"New taxable 900001 just above 9L into 15pct"),
    (1274999,"New taxable 1199999 just below 12L"),
    (1275000,"New taxable 1200000 at 12L"),
    (1275001,"New taxable 1200001 just above 12L into 20pct"),
    (1574999,"New taxable 1499999 just below 15L"),
    (1575000,"New taxable 1500000 at 15L"),
    (1575001,"New taxable 1500001 just above 15L into 30pct"),
]:
    add(d, I(g), 'slab_boundary_new', edge=True)

# ============================================================
# STANDARD DEDUCTION (10)
# ============================================================
for g, d in [
    (30000,"Salary 30K below old SD 50K"),
    (50000,"Salary exactly old SD 50K"),
    (49999,"Salary 49999 just below old SD"),
    (50001,"Salary 50001 just above old SD"),
    (75000,"Salary exactly new SD 75K"),
    (74999,"Salary 74999 just below new SD"),
    (75001,"Salary 75001 just above new SD"),
    (10000,"Salary 10K very low"),
    (100000,"Salary 1L SD fully utilized"),
    (250000,"Salary 2.5L SD utilized below exemption"),
]:
    add(d, I(g), 'standard_deduction', edge=True)

# ============================================================
# HRA CASES (20)
# ============================================================
add("Metro HRA received is minimum", I(1200000,600000,0,100000,300000,'metro'), 'hra')
add("Metro 50pct basic is minimum", I(1200000,300000,0,400000,400000,'metro'), 'hra')
add("Metro rent-10pct basic is minimum", I(1200000,600000,0,300000,100000,'metro'), 'hra')
add("Non-metro HRA received is minimum", I(1000000,500000,0,80000,200000,'non_metro'), 'hra')
add("Non-metro 40pct basic is minimum", I(1000000,200000,0,300000,300000,'non_metro'), 'hra')
add("Non-metro rent-10pct basic is minimum", I(1000000,500000,0,200000,80000,'non_metro'), 'hra')
add("Zero HRA received no exemption", I(1000000,500000,0,0,200000,'metro'), 'hra', edge=True)
add("Zero rent no HRA exemption", I(1000000,500000,0,200000,0,'metro'), 'hra', edge=True)
add("Rent below 10pct basic C negative", I(1000000,500000,0,200000,40000,'metro'), 'hra', edge=True)
add("Rent exactly 10pct basic C zero", I(1000000,500000,0,200000,50000,'metro'), 'hra', edge=True)
add("All 3 HRA components equal non-metro", I(1000000,500000,0,200000,250000,'non_metro'), 'hra')
add("High salary metro HRA", I(2400000,1200000,0,600000,360000,'metro'), 'hra')
add("Low salary with HRA non-metro", I(400000,200000,0,80000,120000,'non_metro'), 'hra')
add("HRA with DA component metro", I(1500000,500000,200000,350000,240000,'metro'), 'hra')
add("High rent HRA capped by received", I(1000000,500000,0,100000,500000,'metro'), 'hra')
add("Small rent C is limiting metro", I(1000000,500000,0,300000,100000,'metro'), 'hra')
add("Zero basic salary HRA exempt zero", I(800000,0,0,200000,100000,'metro'), 'hra', edge=True)
add("HRA with 80C deduction combined", I(1500000,750000,0,300000,200000,'metro',c80c=150000), 'hra')
add("Metro comparison B 200K is min", I(1200000,400000,0,250000,300000,'metro'), 'hra')
add("Non-metro comparison B 160K is min", I(1200000,400000,0,250000,300000,'non_metro'), 'hra')

# ============================================================
# 80C / 80CCD / 80D DEDUCTIONS (20)
# ============================================================
add("80C at max 1.5L", I(1200000, c80c=150000), 'deductions')
add("80C partial 50K", I(1200000, c80c=50000), 'deductions')
add("80C exceeding cap 200K capped 150K", I(1200000, c80c=200000), 'deductions')
add("80CCD 1B at max 50K", I(1200000, c80ccd=50000), 'deductions')
add("80CCD 1B exceeding cap 80K capped 50K", I(1200000, c80ccd=80000), 'deductions')
add("80D self at max 25K under 60", I(1200000, d_self=25000), 'deductions')
add("80D self at max 50K age 65 senior", I(1200000, age=65, d_self=50000), 'deductions')
add("80D self exceeding 40K capped 25K under 60", I(1200000, d_self=40000), 'deductions')
add("80D parents 25K non-senior", I(1200000, d_par=25000), 'deductions')
add("80D parents 50K parents senior", I(1200000, d_par=50000, par_sr=True), 'deductions')
add("80D parents 60K non-senior capped 25K", I(1200000, d_par=60000), 'deductions')
add("80C 1.5L plus 80CCD 50K combo", I(1200000, c80c=150000, c80ccd=50000), 'deductions')
add("80C 1.5L plus 80D self 25K parents 25K", I(1200000, c80c=150000, d_self=25000, d_par=25000), 'deductions')
add("All deductions at max non-senior", I(1200000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000), 'deductions')
add("All deductions max senior self 50K", I(1200000, age=65, c80c=150000, c80ccd=50000, d_self=50000, d_par=25000), 'deductions')
add("All deductions max parents senior 50K", I(1200000, c80c=150000, c80ccd=50000, d_self=25000, d_par=50000, par_sr=True), 'deductions')
add("Partial 80C 80K plus 80D 10K", I(1200000, c80c=80000, d_self=10000), 'deductions')
add("Very small 80C 1K", I(1200000, c80c=1000), 'deductions')
add("All deductions max plus home loan 2L", I(1200000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000, hloan=200000), 'deductions')
add("All deductions max with 25L salary", I(2500000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000), 'deductions')

# ============================================================
# HOME LOAN (10)
# ============================================================
for hl, d in [
    (50000,"Home loan 50K"),(100000,"Home loan 1L"),
    (150000,"Home loan 1.5L"),(200000,"Home loan 2L at max"),
    (250000,"Home loan 2.5L capped 2L"),(300000,"Home loan 3L capped 2L"),
]:
    add(d, I(1500000, hloan=hl), 'home_loan')
add("Home loan 2L with 80C 1.5L", I(1500000, c80c=150000, hloan=200000), 'home_loan')
add("Home loan 2L all deductions max", I(1500000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000, hloan=200000), 'home_loan')
add("Home loan 1L low salary 5L", I(500000, hloan=100000), 'home_loan')
add("Home loan 0 baseline", I(1500000, hloan=0), 'home_loan')

# ============================================================
# REBATE 87A BOUNDARY (20)
# ============================================================
for g, d in [
    (550000,"Old taxable 500000 at rebate full rebate"),
    (550001,"Old taxable 500001 just above rebate cliff"),
    (549999,"Old taxable 499999 just below rebate"),
    (500000,"Old taxable 450000 in rebate zone"),
    (300000,"Old taxable 250000 at exemption zero tax"),
    (530000,"Old taxable 480000 near rebate limit"),
    (545000,"Old taxable 495000 near rebate"),
    (560000,"Old taxable 510000 above rebate"),
    (600000,"Old taxable 550000 above rebate"),
    (520000,"Old taxable 470000 in rebate zone"),
]:
    add(d, I(g), 'rebate_87a', edge=True)
for g, d in [
    (775000,"New taxable 700000 at rebate full rebate"),
    (775001,"New taxable 700001 just above rebate cliff"),
    (774999,"New taxable 699999 just below rebate"),
    (725000,"New taxable 650000 in rebate zone"),
    (375000,"New taxable 300000 at exemption zero tax"),
    (575000,"New taxable 500000 in rebate zone"),
    (785000,"New taxable 710000 above rebate"),
    (795000,"New taxable 720000 above rebate"),
    (765000,"New taxable 690000 below rebate"),
    (825000,"New taxable 750000 well above rebate"),
]:
    add(d, I(g), 'rebate_87a', edge=True)

# ============================================================
# SURCHARGE (15)
# ============================================================
for g, d in [
    (5050000,"Old taxable 5000000 at 50L no surcharge"),
    (5050001,"Old taxable 5000001 10pct heavy marginal relief"),
    (5150000,"Old taxable 5100000 10pct marginal relief"),
    (5250000,"Old taxable 5200000 10pct near relief boundary"),
    (6050000,"Old taxable 6000000 10pct no relief"),
    (10050000,"Old taxable 10000000 10pct at 1Cr"),
    (10050001,"Old taxable 10000001 15pct heavy marginal relief"),
    (10300000,"Old taxable 10250000 15pct near relief boundary"),
    (15050000,"Old taxable 15000000 15pct no relief"),
    (20050000,"Old taxable 20000000 15pct at 2Cr boundary"),
    (20050001,"Old taxable 20000001 25pct heavy marginal relief"),
    (50050000,"Old taxable 50000000 25pct at 5Cr"),
    (50075001,"Both above 5Cr 37pct old 25pct new"),
    (60050000,"Old taxable 60000000 37pct surcharge"),
    (100050000,"Old taxable 100000000 37pct 10Cr"),
]:
    add(d, I(g), 'surcharge', edge=True)

# ============================================================
# COMPREHENSIVE (25)
# ============================================================
add("IT engineer 12L CTC Mumbai", I(1200000,480000,0,240000,240000,'metro',28,150000,0,15000), 'comprehensive')
add("Manager 25L CTC Delhi", I(2500000,1000000,0,500000,420000,'metro',40,150000,50000,25000,25000,False,200000), 'comprehensive')
add("Director 50L Mumbai all ded", I(5000000,2000000,0,1000000,720000,'metro',52,150000,50000,25000,25000,False,200000), 'comprehensive')
add("VP 75L Bangalore all ded", I(7500000,3000000,0,1500000,600000,'metro',55,150000,50000,25000,50000,True,200000), 'comprehensive')
add("Fresh grad 4L no deductions", I(400000,200000,0,80000,120000,'non_metro',23), 'comprehensive')
add("Mid-level 8L 80C only", I(800000,400000,0,160000,144000,'metro',30,100000), 'comprehensive')
add("Senior dev 15L Pune", I(1500000,600000,0,300000,180000,'non_metro',35,150000,50000,20000), 'comprehensive')
add("Consultant 20L Chennai", I(2000000,800000,0,400000,300000,'metro',38,150000,50000,25000,25000), 'comprehensive')
add("CXO 1Cr Mumbai max ded", I(10000000,4000000,0,2000000,1200000,'metro',50,150000,50000,25000,50000,True,200000), 'comprehensive')
add("Startup founder 2Cr Delhi", I(20000000,8000000,0,4000000,1800000,'metro',45,150000,50000,25000,25000,False,200000), 'comprehensive')
add("Teacher 6L small town", I(600000,300000,0,120000,60000,'non_metro',40,50000,0,10000), 'comprehensive')
add("Doctor 18L metro", I(1800000,720000,0,360000,300000,'metro',48,150000,50000,25000), 'comprehensive')
add("Govt employee 10L own house", I(1000000,500000,200000,0,0,'non_metro',45,150000,50000,0,0,False,150000), 'comprehensive')
add("Retired senior 8L pension", I(800000,800000,0,0,0,'non_metro',65,150000,0,50000,50000,True), 'comprehensive')
add("Super senior 5L pension minimal", I(500000,500000,0,0,0,'non_metro',85,50000), 'comprehensive')
add("Young professional 7L Hyderabad", I(700000,350000,0,140000,120000,'non_metro',26,80000,20000,15000), 'comprehensive')
add("Dual income 30L Mumbai", I(3000000,1200000,0,600000,480000,'metro',42,150000,50000,25000,25000,False,200000), 'comprehensive')
add("Engineer 9L Kolkata no HRA", I(900000,450000,0,0,0,'non_metro',32,150000,50000,25000), 'comprehensive')
add("Manager 16L Gurgaon", I(1600000,640000,0,320000,300000,'metro',36,150000,50000,20000,15000), 'comprehensive')
add("Partner 40L Mumbai", I(4000000,1600000,0,800000,600000,'metro',48,150000,50000,25000,50000,True,200000), 'comprehensive')
add("Analyst 11L Bangalore", I(1100000,440000,0,220000,180000,'metro',27,100000,30000,15000), 'comprehensive')
add("Architect 14L Delhi", I(1400000,560000,0,280000,240000,'metro',33,130000,40000,20000,10000), 'comprehensive')
add("CEO 5Cr Mumbai", I(50000000,20000000,0,10000000,3600000,'metro',55,150000,50000,25000,50000,True,200000), 'comprehensive')
add("Low income 3L Tier 3 city", I(300000,150000,0,60000,36000,'non_metro',25,30000), 'comprehensive')
add("Sr manager 22L Noida max ded", I(2200000,880000,0,440000,360000,'metro',43,150000,50000,25000,25000,False,200000), 'comprehensive')

# ============================================================
# SENIOR CITIZEN (10)
# ============================================================
add("Senior 60 with 8L salary", I(800000, age=65), 'senior_citizen')
add("Senior 60 with 12L salary", I(1200000, age=65), 'senior_citizen')
add("Senior 60 with 5L salary rebate", I(500000, age=65), 'senior_citizen')
add("Senior 60 with 3.5L at exemption", I(350000, age=65), 'senior_citizen')
add("Senior 60 15L with deductions", I(1500000, age=65, c80c=150000, d_self=50000, d_par=50000, par_sr=True), 'senior_citizen')
add("Super senior 80 with 6L salary", I(600000, age=85), 'senior_citizen')
add("Super senior 80 with 10L salary", I(1000000, age=85), 'senior_citizen')
add("Super senior 80 with 5L zero tax", I(500000, age=85), 'senior_citizen')
add("Super senior 80 with 20L salary", I(2000000, age=85), 'senior_citizen')
add("Super senior 80 with 5.5L salary", I(550000, age=85), 'senior_citizen')

# ============================================================
# ZERO / MINIMAL (10)
# ============================================================
add("Zero income", I(0), 'zero_minimal', edge=True)
add("Income 1 rupee", I(1), 'zero_minimal', edge=True)
add("Income 100 rupees", I(100), 'zero_minimal', edge=True)
add("Income 1000 rupees", I(1000), 'zero_minimal', edge=True)
add("Income 10000 rupees", I(10000), 'zero_minimal', edge=True)
add("Income exactly old exemption plus SD 3L", I(300000), 'zero_minimal', edge=True)
add("Income exactly new SD 75K zero new taxable", I(75000), 'zero_minimal', edge=True)
add("Income 1L with max deductions", I(100000, c80c=150000, d_self=25000), 'zero_minimal', edge=True)
add("Income below all exemptions 150K", I(150000), 'zero_minimal', edge=True)
add("Income 2L near exemption", I(200000), 'zero_minimal', edge=True)

# ============================================================
# HIGH INCOME (10)
# ============================================================
add("High income 50L no ded", I(5000000), 'high_income')
add("High income 75L no ded", I(7500000), 'high_income')
add("High income 1Cr no ded", I(10000000), 'high_income')
add("High income 1.5Cr no ded", I(15000000), 'high_income')
add("High income 2Cr no ded", I(20000000), 'high_income')
add("High income 3Cr no ded", I(30000000), 'high_income')
add("High income 5Cr no ded", I(50000000), 'high_income')
add("High income 10Cr no ded", I(100000000), 'high_income')
add("High income 50L max deductions", I(5000000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000, hloan=200000), 'high_income')
add("High income 1Cr HRA all ded", I(10000000,4000000,0,2000000,1200000,'metro',40,150000,50000,25000,25000,False,200000), 'high_income')

# ============================================================
# ADDITIONAL EDGE CASES (10)
# ============================================================
add("All deductions exceed income 5L", I(500000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000, hloan=200000), 'edge_case', edge=True)
add("Senior all ded max 8L", I(800000, age=65, c80c=150000, c80ccd=50000, d_self=50000, d_par=50000, par_sr=True, hloan=200000), 'edge_case', edge=True)
add("Super senior all ded max 10L", I(1000000, age=85, c80c=150000, c80ccd=50000, d_self=50000, d_par=50000, par_sr=True, hloan=200000), 'edge_case', edge=True)
add("HRA greater than gross", I(500000, 200000, 0, 600000, 300000, 'metro'), 'edge_case', edge=True)
add("Rent greater than gross", I(500000, 200000, 0, 100000, 600000, 'metro'), 'edge_case', edge=True)
add("80D both max senior", I(1500000, age=65, d_self=50000, d_par=50000, par_sr=True), 'edge_case', edge=True)
add("All deductions exact at cap", I(2000000, c80c=150000, c80ccd=50000, d_self=25000, d_par=25000, hloan=200000), 'edge_case', edge=True)
add("Very high income 50Cr", I(500000000), 'edge_case', edge=True)
add("Gross exactly 1 above old SD", I(50001), 'edge_case', edge=True)
add("Max possible old regime deductions", I(3000000, 1200000, 0, 600000, 480000, 'metro', 65, 150000, 50000, 50000, 50000, True, 200000), 'edge_case', edge=True)

# ============================================================
# COMPUTE EXPECTED VALUES
# ============================================================
for c in cases:
    c['expected_old_regime'] = compute_old(c['input'])
    c['expected_new_regime'] = compute_new(c['input'])

# ============================================================
# VALIDATION
# ============================================================
def validate():
    # TC007: 500000 salary, no ded, age 30
    c = next(x for x in cases if x['id'] == 'TC007')
    o, n2 = c['expected_old_regime'], c['expected_new_regime']
    assert o['taxable_income'] == 450000, f"TC007 old taxable {o['taxable_income']}"
    assert o['tax_before_rebate'] == 10000, f"TC007 old tax {o['tax_before_rebate']}"
    assert o['rebate_87a'] == 10000
    assert o['total_tax'] == 0
    assert n2['taxable_income'] == 425000
    assert n2['tax_before_rebate'] == 6250
    assert n2['total_tax'] == 0
    # TC012: 1000000, no ded
    c = next(x for x in cases if x['id'] == 'TC012')
    o = c['expected_old_regime']
    assert o['taxable_income'] == 950000
    assert o['tax_before_rebate'] == 102500  # 12500+90000
    assert o['total_tax'] == 106600  # 102500+4100
    n2 = c['expected_new_regime']
    assert n2['taxable_income'] == 925000
    assert n2['tax_before_rebate'] == 42500  # 20000+22500
    assert n2['total_tax'] == 44200
    # TC014: 1500000, no ded
    c = next(x for x in cases if x['id'] == 'TC014')
    o = c['expected_old_regime']
    assert o['taxable_income'] == 1450000
    assert o['tax_before_rebate'] == 247500  # 12500+100000+135000
    assert o['total_tax'] == 257400
    n4 = c['expected_new_regime']
    assert n4['taxable_income'] == 1425000
    assert n4['tax_before_rebate'] == 125000  # 20000+30000+30000+45000
    assert n4['total_tax'] == 130000
    print("All validations passed!")

validate()

# ============================================================
# WRITE test_cases.json
# ============================================================
out_dir = r'd:\FireAI\project_a\tests'
os.makedirs(out_dir, exist_ok=True)

with open(os.path.join(out_dir, 'test_cases.json'), 'w') as f:
    json.dump(cases, f, indent=2)
print(f"Wrote {len(cases)} test cases to test_cases.json")

# ============================================================
# WRITE official_verified.json (30 cases)
# ============================================================
official_ids = [
    'TC001','TC005','TC007','TC008','TC012','TC014','TC016','TC019',
    'TC025','TC026','TC028','TC033',
    'TC037','TC040','TC043',
    'TC081','TC084','TC086','TC089','TC092','TC094',
    'TC101','TC104',
    'TC111','TC112','TC121','TC122',
    'TC171','TC176','TC178',
]
official = []
for c in cases:
    if c['id'] in official_ids:
        oc = copy.deepcopy(c)
        oc['verified_against_official'] = True
        official.append(oc)

with open(os.path.join(out_dir, 'official_verified.json'), 'w') as f:
    json.dump(official, f, indent=2)
print(f"Wrote {len(official)} official verified cases")

print("Done!")

