def repeater(values):
    i = 0
    while True:
        yield values[i]
        i += 1
        if i >= len(values):
            i = 0

it = repeater([1,2,3,4,5])
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
print(next(it))
'''
from termctrl import *
    
term = TermCtrl()
term.setserverlist()
term.connectlist()
term.showclients()
sftp = term.server_list['client'][0][2]
client = term.server_list['client'][0][1]
cmdrun = CMDRunner()
ftr = FTRunner()
ftr.putfile(sftp, 'termctrl.py', '/root/termctrl.py')
print(cmdrun.runcmd(client, 'ls -al'))
'''
'''
#sess.connectlist()
print(term.cinf)

ssh1 = term.cinf['client'][0]
tel2 = term.cinf['client'][1]
tel3 = term.cinf['client'][3]
tel4 = term.cinf['client'][4]

ret1 = term.runcmdshell(ssh1[1], ['cat /home/trollking/test.txt'])
ret2 = term.runcmdshell(tel2, ['cat /home/trollking/test.txt'])
ret3 = term.runcmdshell(tel3, ['cat /home/trollking/test.txt'])
ret4 = term.runcmdshell(tel4, ['cat /home/trollking/test.txt'])

print(ret1['recv'])
print(ret2['recv'])
print(ret3['recv'])
print(ret4['recv'])
'''