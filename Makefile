run:
	 uvicorn main:app --host 192.168.1.36
 run_dlp:
	 uvicorn main:app --host 0.0.0.0

run_spb:
	uvicorn main:app --host 192.168.0.193
local:
	uvicorn main:app --reload