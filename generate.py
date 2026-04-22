class State:
    def __init__(self, N):
        self.data = [[None for _ in range(N)] for _ in range(N)]
        self.Hconstrain = [[None for _ in range(N-1)] for _ in range(N)]
        self.Vconstrain = [[None for _ in range(N)] for _ in range(N-1)]

mapping = {}
counter = 1
def get_var(literal):
    global counter
    if literal not in mapping:
        mapping[literal] = counter
        counter += 1
    return mapping[literal]
def GroudKB(N,state : State):  
    # listGoundKB = [ 
    #                   [1, 2, ....],
    #                   [N, N+1, ....],
    #                   ...
    #               ]             
    #     each row is CNF clause, each integer stand for one literal
                                        
    listGoundKB = []                                    
    #A1
    #listGoundKB.append("A1") 
    for i in range(N):
        for j in range(N):
            tempRow = []
            for v in range(N):
                tempRow.append(get_var(("Val",i,j,v)))
            listGoundKB.append(tempRow)
    
    #A2
    #listGoundKB.append("A2")
    for i in range(N):
        for j in range(N):
            for v1 in range(N):
                for v2 in range(v1 +1, N, 1):
                    listGoundKB.append([
                        -get_var(("Val",i,j,v1)),
                        -get_var(("Val",i,j,v2))
                    ])
    
    #A3
    #listGoundKB.append("A3")
    for i in range(N):
        for j1 in range(N):
            for j2 in range(j1 +1, N, 1):
                for v in range(N):
                    listGoundKB.append([
                        -get_var(("Val",i,j1,v)),
                        -get_var(("Val",i,j2,v))
                    ])

    #A4
    #listGoundKB.append("A4")
    for j in range(N):
        for i1 in range(N):
            for i2 in range(i1 +1, N, 1):
                for v in range(N):
                    listGoundKB.append([
                        -get_var(("Val",i1,j,v)),
                        -get_var(("Val",i2,j,v))
                    ])
    
    #A5
    #listGoundKB.append("A5")
    for i in range(N):
        for j in range(N-1):
            if state.Hconstrain[i][j] == 1:
                for v1 in range(N):
                    for v2 in range(0, v1+1, 1):
                        listGoundKB.append([
                            -get_var(("Val",i,j,v1)),
                            -get_var(("Val",i,j+1,v2))
                        ])
    
    #A6
    #listGoundKB.append("A6")
    for i in range(N):
        for j in range(N-1):
            if state.Hconstrain[i][j] == -1:
                for v1 in range(N): 
                    for v2 in range(v1, N, 1):
                        listGoundKB.append([
                            -get_var(("Val",i,j,v1)),
                            -get_var(("Val",i,j+1,v2))
                        ])
    
    #A7
    #listGoundKB.append("A7")
    for j in range(N):
        for i in range(N-1):
            if state.Vconstrain[i][j] == 1:
                for v1 in range(N):
                    for v2 in range(0, v1+1, 1):
                        listGoundKB.append([
                            -get_var(("Val",i,j,v1)),
                            -get_var(("Val",i+1,j,v2))
                        ])

        
    #A8
    #listGoundKB.append("A8")
    for j in range(N):
        for i in range(N-1):
            if state.Vconstrain[i][j] == -1:
                for v1 in range(N): 
                    for v2 in range(v1, N, 1):
                        listGoundKB.append([
                            -get_var(("Val",i,j,v1)),
                            -get_var(("Val",i+1,j,v2))
                        ])

    #A9
    #listGoundKB.append("A9")
    for i in range(N):
        for j in range(N):
            if state.data[i][j] != -1:
                listGoundKB.append([get_var(("Val",i,j,state.data[i][j]))])

    return listGoundKB



if __name__ == "__main__":
    with open("input.txt") as f:
        N = int(f.readline().strip())
        InitState = State(N)
        i = 0
        line = f.readline().strip()
        while(line := f.readline().strip()):
            Row = list(map(int,line.split(',')))
            for j in range(N):
                InitState.data[i][j] = Row[j] - 1
            i += 1

        i = 0
        while(line := f.readline().strip()):
            Row = list(map(int,line.split(',')))
            for j in range(N-1):
                InitState.Hconstrain[i][j] = Row[j]
            i += 1 
        
        i = 0
        while(line := f.readline().strip()):
            Row = list(map(int,line.split(',')))
            for j in range(N):
                InitState.Vconstrain[i][j] = Row[j]
            i += 1 

    list = GroudKB(N,InitState)
    
    
        
