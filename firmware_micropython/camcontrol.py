#!/bin/python3
import sys, time, subprocess, socket

if __name__ == '__main__':
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('0.0.0.0', 8081))
    s.listen()
    while True:
      try:
        conn, addr = s.accept()
        with conn:
          print(f"{addr} connected")
          while True:
            req = conn.recv(1024)
            print(req)
            if not req:
              break
            print("connection valid")
            subprocess.run(["gphoto2", "--capture-image"]) 
            cs.write('')
            cs.close()
      except Exception as e:
        print("ERROR " + str(e))
