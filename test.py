from termctrl import *
    
term = TermCtrl()
term.setserverlist()
term.connectlist()
term.showclients()
client = term.server_list['client'][0][1]
cmdrun = CMDRunner()
print(cmdrun.runcmd(client, 'ls -al'))
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