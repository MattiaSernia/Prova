from datetime import datetime

def text_handling(testo):
    testo=testo.split("| ")
    date= testo[0].rstrip(" ")
    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S,%f")
    mxg = testo[2]
    nodemxg= testo[2].split(": ")[1:]
    if len(nodemxg)>1:
        new= ""
        for element in nodemxg:
            new=new+" "+element
        nodemxg=new
    else: 
        nodemxg=nodemxg[0]
    return nodemxg, mxg, date