#simple websockets brocaster
import asyncio
import websockets
import json
clients = [] #to store all connected cleints
players = []#儲存玩家
line = []#儲存觀看者
state = [[0 for i in range(5)] for j in range(5)]#5*5的二維矩陣

async def broadcast_click(msg):
    m = msg.split("#")#將#賦予m值
    await broadcast(m[0])#將m列表的第一个元素作為參數傳入
    print(msg,'number')
    for websock in line:
        try:
            await websock.send(msg) #send message to each client
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected. Do cleanup")
            clients.remove(websock)
async def broadcast(msg):
    print(msg,'number')
    for websock in clients:
        if websock not in line:
            try:
                await websock.send(msg) #send message to each client
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected. Do cleanup")
                clients.remove(websock)
        
async def color(msg):
    print(msg,'color')
    for websock in players:
        try:
            await websock.send(msg) #send message to each client
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected. Do cleanup")
            clients.remove(websock)


#handler for socket message activities
async def handler(websocket, path):
	#print(path) #path is not used currently
    if websocket not in clients:
        clients.append(websocket) #append new cleint to the array
    async for message in websocket:
        #全域變數
        global players
        global state
        global line
        msg = message.split('#')
        print(msg,'received from client') #print to console
        #收到play時，玩家人數有沒有大於2
        if msg[0]=="play":
            if len(players)>=2:
                line.append(websocket)
                #發送消息
                await websocket.send("對戰...")
            else:
                #當前有幾個在裡面
                players.append(websocket)
                n = len(players)
                n = str(n)
                await broadcast_click(n+"#prepare")
            #number會通知，有哪些玩家準備好
        elif msg[0] == "number":
            n = len(players)
            n = str(n)
            if len(players)>=2:
                await websocket.send("對戰...")
            else:
                await broadcast(n)
        elif msg[0] == "land":
            #一個玩家是左邊的玩家
            left = players[0]
            #字串轉為int
            msg[1] = str(msg[1])
            #看msg[1]裡的值下在哪一列或哪一行
            row = int(msg[1][1])
            col= int(msg[1][0])
            #state去改變位置上要加一還是減一
            if websocket == left:
                state[row][col] = state[row][col] + 1
                r = msg[1][1]
                c = msg[1][0]
                point = str(state[row][col])
                #告訴棋盤上是要變成哪個顏色
                await color(r+"#"+c+"#"+point+"#"+"notify")
            else:
                state[row][col] = state[row][col] - 1
                r = msg[1][1]
                c = msg[1][0]
                point = str(state[row][col])
                await color(r+"#"+c+"#"+point+"#"+"notify")
        elif msg[0] == "stop":
            #玩家的分數都設為0
            count_l = 0
            count_r = 0
            winner = 0
            #在這邊統計說大於0或小於0有幾個數
            for i in range(len(state)):
                for j in range(len(state)):
                    if state[i][j]>0:
                        count_l = count_l + 1
                    elif state[i][j]<0:
                        count_r = count_r + 1
            if count_l<count_r:
                winner = 1
            elif count_l == count_r:
                winner = 2
                #轉為字串，再呼叫color，傳達結束的消息
            count_l = str(count_l)
            count_r = str(count_r)
            winner = str(winner)
            await color(count_l+"#"+count_r+"#"+winner+"#"+"end")
        #清空全部，然後重新開始
        elif msg[0] == "out":
            players = []
            n = len(players)
            n = str(n)
            state = [[0 for i in range(5)] for j in range(5)]
            await broadcast_click(n+"#prepare")
#starts the service and run forever
loop = asyncio.new_event_loop() #get an event loop
asyncio.set_event_loop(loop) #set the event loop to asyncio
loop.run_until_complete(
	websockets.serve(handler,'localhost', 4545) #setup the websocket service and handler
	) #hook to localhost:4545
loop.run_forever() #keep it running