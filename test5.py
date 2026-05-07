from numpy import array
from random import randint
def saisir():
    global n
    n=int(input("n="))
    while n<2 or n>20:
        n=int(input("n="))
def alpha(ch):
    test=True
    i=0
    ch=ch.upper()
    while i<len(ch) and test==True:
        if "A"<=ch[i] and ch[i]<="Z":
            i=i+1
        else:
            test=False
    return test
def remplir(nom,n):
    for i in range(n):
        nom[i]=input("nom[i]=")
        while alpha(nom[i])==False :
            nom[i]=input("retapez nom[i]=")
def generer(t,n) :
    for i in range (n):
        ch=""
        for j in range(n):
            x=randint(1,3)
            if x==1:
                c=chr(randint(65,90))
            elif x==2:
               c=chr(randint(97,122))
            else:
                c=chr(randint(48,57))
            ch=ch+c
        t[i]=ch

def afficher(nom,mdp,n):
    for i in range (n):
        print(nom[i],':',mdp[i])




saisir()
nom=array([str]*n)
remplir(nom,n)
mdp=array([str]*n)
generer(mdp,n)
afficher(nom,mdp,n)
        
                
                
            
