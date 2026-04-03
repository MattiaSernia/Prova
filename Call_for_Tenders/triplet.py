class Triplet:
    def __init__(self, subject, predicate, object):
        self.subject=subject
        self.predicate=predicate
        self.object=object

    def toString(self):
        return "[ "+self.subject+" | "+self.predicate+ " | "+self.object + " ]"
    
    def getSubject(self):
        return self.subject
    
    def getPredicate(self):
        return self.predicate   
     
    def getObject(self):
        return self.object