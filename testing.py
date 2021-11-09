import machine
import os
import micropython



def timetest(call, runs=5):
    count=0

    times = []

    while count < runs:
        start = time.time_ns()
        eval(call)
        end = time.time_ns()
        times.append((end-start)/1000000000)
        count = count + 1
        print(f"Run time = {(end-start)/1000000000} seconds")

    total=0
    for i in times:
        total = total + i

    avg = total / len(times)
    print(f"Avg run time = {avg}, n = {runs}")



def compare(old, new):
    print(f"New was {old-new} seconds faster ({round((old-new)/old*100, 2)}%) than Old")



def reload_config():
    global config
    with open('config.json', 'r') as file:
        config = json.load(file)
