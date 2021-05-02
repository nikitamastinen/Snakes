run_dlp:
	 uvicorn main:app --host 192.168.1.36
run_spb:
	uvicorn main:app --host 192.168.0.196
local:
	uvicorn main:app --reload