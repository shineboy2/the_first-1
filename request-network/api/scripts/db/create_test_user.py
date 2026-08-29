import json, http.client
conn = http.client.HTTPConnection('127.0.0.1',8001)
payload = json.dumps({"username":"testuser1","email":"testuser1@example.com","password":"TestPass123!","profile_type":"user"})
headers = {'Content-Type':'application/json','Authorization':'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYjUzYTIzZDAtNDgyMS00M2QyLThkOTYtNjIyMGJiYjAyMjRmIiwic2NvcGVzIjpbImFkbWluIl0sImV4cCI6MTc2MzI4MzM4OX0._nErjKfcy_0h5TKrHQelw-EONA-rJgtlFKyjcklCDWM'}
conn.request('POST','/api/v1/users',payload,headers)
res=conn.getresponse()
print(res.status, res.reason)
print(res.read().decode())
