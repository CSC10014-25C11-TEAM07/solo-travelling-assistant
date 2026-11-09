"""Local development backend for Solo Travelling Assistant (S01–S03)."""
import os
import re
import json
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title='Solo Travelling Assistant')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
DB = Path(__file__).with_name('app.sqlite3')
def connect():
    db=sqlite3.connect(DB)
    db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, salt TEXT, hash TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER, expires TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, user_id INTEGER, status TEXT, payload TEXT)')
    db.commit()
    return db
class Credentials(BaseModel):
    username:str
    password:str
class DraftInput(BaseModel):
    departure_date:str
    return_date:str
    departure_time:str
    min_rest_minutes:int
    interests:list[str]
def auth(authorization:str|None):
    if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'Vui lòng đăng nhập.')
    t=authorization[7:]
    with connect() as db:
        row=db.execute('SELECT users.id,users.username FROM sessions JOIN users ON sessions.user_id=users.id WHERE sessions.token=? AND sessions.expires>?',(t,datetime.now(timezone.utc).isoformat())).fetchone()
    if not row:raise HTTPException(401,'Phiên đã hết hạn.')
    return dict(row)
@app.get('/health')
def health():return {'status':'ok'}
@app.post('/api/v1/auth/register',status_code=201)
def register(body:Credentials):
    username=body.username.strip().lower()
    if not re.fullmatch(r'[a-z0-9_]{3,30}',username):raise HTTPException(422,'Tên đăng nhập cần 3–30 ký tự a-z, số hoặc _.')
    if not 4<=len(body.password)<=128:raise HTTPException(422,'Mật khẩu cần 4–128 ký tự.')
    salt=secrets.token_bytes(16)
    digest=pbkdf2_hmac('sha256',body.password.encode(),salt,600000)
    try:
        with connect() as db:db.execute('INSERT INTO users(username,salt,hash) VALUES(?,?,?)',(username,salt.hex(),digest.hex()))
    except sqlite3.IntegrityError:raise HTTPException(409,'Tên đăng nhập đã tồn tại.')
    return {'username':username}
@app.post('/api/v1/auth/login')
def login(body:Credentials):
    with connect() as db:
        row=db.execute('SELECT * FROM users WHERE username=?',(body.username.strip().lower(),)).fetchone()
        if not row or not compare_digest(pbkdf2_hmac('sha256',body.password.encode(),bytes.fromhex(row['salt']),600000),bytes.fromhex(row['hash'])):raise HTTPException(401,'Tên đăng nhập hoặc mật khẩu không đúng.')
        t=secrets.token_urlsafe(32)
        db.execute('INSERT INTO sessions VALUES(?,?,?)',(t,row['id'],(datetime.now(timezone.utc)+timedelta(days=30)).isoformat()))
    return {'access_token':t,'token_type':'bearer'}
@app.get('/api/v1/auth/me')
def me(authorization:str|None=Header(None)):return auth(authorization)
@app.post('/api/v1/auth/logout')
def logout(authorization:str|None=Header(None)):
    auth(authorization)
    with connect() as db:db.execute('DELETE FROM sessions WHERE token=?',(authorization[7:],))
    return {'message':'Đã đăng xuất'}
@app.get('/api/v1/places/recommendations')
def recommendations(interests:list[str]|None=None,authorization:str|None=Header(None)):
    auth(authorization)
    return {'places':[{'place_id':'P01','name':'Hồ Xuân Hương','image_url':None,'reason':'Không gian hồ thơ mộng'}, {'place_id':'P02','name':'Ga Đà Lạt','image_url':None,'reason':'Kiến trúc cổ đặc trưng'}, {'place_id':'P03','name':'Chợ đêm Đà Lạt','image_url':None,'reason':'Ẩm thực địa phương'}]}
def find_trip(id,user):
    with connect() as db:row=db.execute('SELECT * FROM trips WHERE id=? AND user_id=?',(id,user['id'])).fetchone()
    if not row:raise HTTPException(404,'Không tìm thấy lịch trình.')
    return json.loads(row['payload'])
def save_trip(trip,user):
    with connect() as db:db.execute('INSERT OR REPLACE INTO trips VALUES(?,?,?,?)',(trip['itinerary_id'],user['id'],trip['status'],json.dumps(trip,ensure_ascii=False)))
@app.post('/api/v1/itineraries/draft')
def draft(body:DraftInput,authorization:str|None=Header(None)):
    user=auth(authorization)
    try:
        start=datetime.strptime(body.departure_date,'%Y-%m-%d').date()
        end=datetime.strptime(body.return_date,'%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(422,'Ngày đi và ngày về không hợp lệ.')
    if end<start:raise HTTPException(422,'Ngày về không được trước ngày đi.')
    days=(end-start).days+1
    if days not in (3,4):raise HTTPException(422,'Hành trình hỗ trợ 3 hoặc 4 ngày.')
    if body.min_rest_minutes<=0:raise HTTPException(422,'Thời gian nghỉ phải lớn hơn 0.')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',body.departure_time):
        raise HTTPException(422,'Giờ xuất phát không hợp lệ.')
    departure_minutes=int(body.departure_time[:2])*60+int(body.departure_time[3:])
    if departure_minutes>7*60:
        raise HTTPException(422,'Vui lòng xuất phát trước 07:00 để đến Đà Lạt vào ban ngày.')
    if body.min_rest_minutes>180:
        raise HTTPException(422,'Thời gian nghỉ tối đa là 180 phút.')
    names=['Hồ Xuân Hương','Ga Đà Lạt','Quảng trường Lâm Viên','Chợ đêm Đà Lạt','Thiền viện Trúc Lâm','Đồi chè Cầu Đất','Quán cà phê ngắm cảnh','Vườn hoa Đà Lạt']
    def clock(minutes):return f'{minutes//60:02d}:{minutes%60:02d}'
    itinerary_days=[]
    for i in range(days):
        activities=[]
        def add(kind,label,start,finish,code):
            activities.append({'activity_id':f'{code}-{i}','type':kind,'name':label,'start_time':clock(start),'end_time':clock(finish),'status':'PENDING'})
        if i==0:
            arrival=departure_minutes+390
            add('TRAVEL','Di chuyển bằng xe máy từ TP.HCM đến Đà Lạt',departure_minutes,arrival,'TRAVEL')
            rest_end=arrival+body.min_rest_minutes
            add('REST','Nghỉ ngơi và ăn uống',arrival,rest_end,'REST')
            cursor=rest_end+15
            for j in range(2):
                if cursor+75>18*60:break
                add('VISIT',names[j],cursor,cursor+75,f'VISIT-{j}')
                cursor+=90
        elif i==days-1:
            add('VISIT',names[(i*2)%len(names)],8*60,9*60+30,'VISIT-0')
            add('REST','Nghỉ ngơi và ăn uống',9*60+30,9*60+30+body.min_rest_minutes,'REST')
            back=max(11*60,9*60+45+body.min_rest_minutes)
            add('TRAVEL','Di chuyển bằng xe máy về TP.HCM',back,back+390,'RETURN')
        else:
            add('VISIT',names[(i*2)%len(names)],8*60+30,10*60,'VISIT-0')
            add('VISIT',names[(i*2+1)%len(names)],10*60+15,11*60+45,'VISIT-1')
            rest_end=11*60+45+body.min_rest_minutes
            add('REST','Nghỉ ngơi và ăn uống',11*60+45,rest_end,'REST')
            if rest_end+105<=18*60:
                add('VISIT',names[(i*2+2)%len(names)],rest_end+15,rest_end+105,'VISIT-2')
        activities.sort(key=lambda a:a['start_time'])
        itinerary_days.append({'day_id':f'D{i+1}','day_number':i+1,'date':(start+timedelta(days=i)).isoformat(),'activities':activities})
    trip={'itinerary_id':secrets.token_hex(12),'status':'DRAFT','version':1,'departure_date':body.departure_date,'return_date':body.return_date,'itinerary_days':itinerary_days}
    save_trip(trip,user);return trip
@app.post('/api/v1/itineraries/{id}/confirm')
def confirm(id:str,authorization:str|None=Header(None)):
    user=auth(authorization);trip=find_trip(id,user);trip['status']='CURRENT';trip['version']+=1;save_trip(trip,user);return trip
@app.get('/api/v1/itineraries/current')
def current(authorization:str|None=Header(None)):
    user=auth(authorization)
    with connect() as db:row=db.execute("SELECT payload FROM trips WHERE user_id=? AND status='CURRENT' ORDER BY rowid DESC LIMIT 1",(user['id'],)).fetchone()
    if not row:raise HTTPException(404,'Chưa có lịch trình đã xác nhận.')
    return json.loads(row['payload'])
class StatusInput(BaseModel):
    status:str
    base_version:int
@app.patch('/api/v1/itineraries/{id}/activities/{activity_id}')
def mark(id:str,activity_id:str,body:StatusInput,authorization:str|None=Header(None)):
    user=auth(authorization);trip=find_trip(id,user)
    if trip['version']!=body.base_version:raise HTTPException(409,'Lịch trình đã thay đổi.')
    found=False
    for day in trip['itinerary_days']:
        for activity in day['activities']:
            if activity['activity_id']==activity_id:activity['status']='DONE';found=True
    if not found:raise HTTPException(404,'Không tìm thấy hoạt động.')
    trip['version']+=1;save_trip(trip,user);return trip
