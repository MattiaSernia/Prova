from requirementsExtractor import RequirementsExtractor
from constraintsExtractor import ConstraintsExtractor

if __name__=="__main__":
    req=RequirementsExtractor("command-r",0)
    con=ConstraintsExtractor("command-r",0)
    with open("file.txt", "r", encoding="utf-8") as f:
        lines=f.readlines()
        text=" ".join(lines)
    lista=req.pipe(text)
    with open("outputRequirements.txt", "w", encoding='utf-8') as o:
        for element in lista:
            o.write(f"{element['category']} | {element['priority']} | {element['subject']} | {element['predicate']} | {element['object']}\n")
    lista2=con.pipe(text)
    with open("outputConstraints.txt", "w", encoding='utf-8') as o:
        for element in lista2:
            o.write(f"{element['constraintType']} | {element['subject']} | {element['predicate']} | {element['object']}\n")