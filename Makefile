run:
	 uvicorn main:app --host 192.168.1.36
local:
	uvicorn main:app --reload