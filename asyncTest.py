from multiprocessing import Process
import socket
import asyncio
'''
GIL 가 걸린 쓰레드를 대신할 async 임시 테스트 코드
'''
async def test():
    pass

async def test2(a):
    pass

def main():
    procs = []
    a = "d"
    proc = Process(target=test2, args=(a,))
    procs.append(proc)
    proc.start()

    proc.join()

if __name__ == '__main__':
    main()