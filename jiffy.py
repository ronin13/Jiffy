#!/usr/bin/env python
# Dont descend into deep directories
# Use some way to avoid cycles
# CLEANUP require

import os
import string
import sys
pattern="MPEG|Flash|Matroska"
filter="sort -r | grep -v wav"
exer="mpc pause &>/dev/null ; /home/raghavendra/bin/mplayer"
import cPickle
#menu="~/bin/dmenu/dmenu  -i -l 3  -fn -*-monospace-*-r-normal-*-12-*-*-*-p-*-*-* -nb cyan4 -nf black -p"
#menu="~/bin/dmenu -p '>' -i -l 5 -nb black -nf yellow -sb black"
menu=os.environ['DMENU']
from subprocess import *
global mdict
mdict={}

import magic
import re
from threading import Thread
from ConfigParser import ConfigParser

workdir=os.path.join(os.environ['XDG_DATA_HOME'],"jiffy")
configdir=os.path.join(os.environ['XDG_CONFIG_HOME'],"jiffy")
if not os.path.exists(workdir):
    os.mkdir(workdir,764)
    os.mkdir(configdir,764)

ofile=os.path.join(workdir,"jiffle")
confile=os.path.join(configdir,"config")
#histfile=os.path.join(workdir,"history")
      
#{{{
class Traverse(Thread):
    def __init__(self,mpath,table,delchars,exer,m):
        Thread.__init__(self)
        self.mpath=mpath
        self.dict={}
        self.table=table
        self.delchars=delchars
        self.exer=exer
        self.m = m

    def run(self):
        dirlist=[]
        try:
            files = os.listdir(self.mpath)
        except:
            return 

        xfile=[]
        for f in files:
            if os.path.isdir(os.path.join(self.mpath,f)):
                current=Traverse(str(os.path.join(self.mpath,f)),self.table,self.delchars,self.exer,self.m)
                dirlist.append(current)
                current.start()
            else:
                xfile+=[f]

        for f in xfile:
            type=str(m.file(os.path.join(self.mpath,f)))
            if re.match("^.*(%s).*$"%pattern,type):
                key=f.translate(self.table,self.delchars)
                key=re.sub("\s+",".",key)
                self.dict[key]=[str(os.path.join(self.mpath,f)),self.exer]

        for thread in dirlist:
            thread.join()
            self.dict.update(thread.dict)
#}}}  
dirlist=[]

if str(sys.argv[1]) == "1":
    table=string.maketrans('','')
    delchars = ''.join([c for c in table if c not in string.letters+string.digits+"_"+"."+" "])

    conf=ConfigParser()
    conf.read([confile])
    media_path=conf.get('General','path').split(',')

    m=magic.open(magic.MAGIC_CHECK)
    m.load()

    for path in media_path:
        current=Traverse(path,table,delchars,exer,m)
        dirlist.append(current)
        current.start()
   
    for thread in dirlist:
        thread.join()
        mdict.update(thread.dict)
        print "%s path done:"%thread.mpath
    
    with open(ofile,"w") as handle:
        p=cPickle.Pickler(handle,2)
        p.dump(mdict)
else:
    key=None
    dic={}
    with open(ofile,"r") as handle:
        p = cPickle.Unpickler(handle)
        dic = p.load()
    files = '"'
    files += string.join(dic.keys(),"\n")
    files += '"'
    dm = Popen("%s | %s "%(filter,menu),shell=True,executable="/bin/sh",stdin=PIPE,stdout=PIPE) 
    key,error = dm.communicate(files)
    if key is None or key == "":
        print "Error %s"%error
        exit(1)
    #else:
    #    print "yay! %s"%key
    #    exit(0)


    #VERY TEMP
    #path,exer=dic[key]
    path=dic[key][0]

    if (not os.path.exists(path)):
        exit(0)
   
    pid = Popen("%s \"%s\" "%(exer,path),shell=True).pid
    
    with open(ofile,"w") as handle:
        if not dic.has_key(":h.%s"%key):
            dic[":h.%s"%key]=[path,exer]
            #dic[":1.%s"%key]=[path,exer,1]
        p=cPickle.Pickler(handle,2)
        p.dump(dic)
