import os, tempfile
fd,path=tempfile.mkstemp(suffix='.db');os.close(fd);os.unlink(path)
os.environ['STA_DB_PATH']=path
from fastapi.testclient import TestClient
from main import app
c=TestClient(app)
assert c.get('/health').json()['status']=='ok'
assert c.post('/api/v1/auth/register',json={'username':'han_test','password':'a-long-password-123'}).status_code==201
assert c.post('/api/v1/auth/register',json={'username':'han_test','password':'a-long-password-123'}).status_code==409
r=c.post('/api/v1/auth/login',json={'username':'han_test','password':'a-long-password-123'});assert r.status_code==200,r.text
h={'Authorization':'Bearer '+r.json()['access_token']}
assert c.get('/api/v1/auth/me',headers=h).status_code==200
assert len(c.get('/api/v1/places/recommendations?interests=nature&interests=coffee',headers=h).json()['places'])<=3
v={'departure_date':'2026-12-10','return_date':'2026-12-13','departure_time':'06:00','interests':['nature','coffee'],'min_rest_minutes':60}
r=c.post('/api/v1/itineraries/draft',json=v,headers=h);assert r.status_code==201,r.text
trip=r.json();assert len(trip['itinerary_days'])==4
id=trip['itinerary_id'];assert trip['status']=='DRAFT'
r=c.post('/api/v1/itineraries/'+id+'/confirm',headers=h);assert r.status_code==200,r.text
trip=r.json();assert trip['status']=='CURRENT'
assert c.get('/api/v1/itineraries/current',headers=h).json()['itinerary_id']==id
aid=trip['itinerary_days'][0]['activities'][0]['activity_id']
url=f'/api/v1/itineraries/{id}/activities/{aid}'
r=c.patch(url,json={'status':'DONE','base_version':trip['version']},headers=h);assert r.status_code==200,r.text
assert c.patch(url,json={'status':'DONE','base_version':trip['version']},headers=h).status_code==409
assert c.get('/api/v1/itineraries/current').status_code==401
assert c.post('/api/v1/auth/logout',headers=h).status_code==200
assert c.get('/api/v1/auth/me',headers=h).status_code==401
os.unlink(path)
print('PASS: health, register, duplicate, login, me, F01, draft, confirm, current, DONE, stale 409, ownership, logout')
