# 时间 ： 2020/12/21 9:44
# 作者 ： Shizhun Xiao
# 文件 ： connect.py
# 项目 ： moziAI_nlz
# 版权 ： 北京华戍防务技术有限公司
import zmq
  
class ScheCom():
  
    def __init__(self):
        
        # ScheRecvRayport: 调度程序与RAY机器通信的接口,ScheRecvRayport数据格式:"字符串",例如:“4785” 
        
        self.Zmq=zmq.Context()
        self.Zmq.setsockopt(zmq.RCVHWM, 1)
        self.Zmq.setsockopt(zmq.SNDHWM, 1)
        
    def Bind_Port(self,BindPort):
        #绑定接口:BindPort
        Req=self.Zmq.socket(zmq.REP)
        Req.bind("tcp://*:%s" %(BindPort)) 
        return Req
   
     
    def Send_Req(self,Req,Req_Port):
        #Ray发送请求到调度程序，Ray_Send_Sche_Port为调度接收端的端口，例如:"192.168.4.1:4785"
        Send_=self.Zmq.socket(zmq.REQ)
        Send_.connect("tcp://%s" %(Req_Port))
        Send_.send_string(Req)
        Response=Send_.recv_string()
        return Response
#test response:

#reply="0"
#Zmq=ScheCom()
#BindOb=Zmq.Bind_Port("5703")
#while True:
    
    #Rev=BindOb.recv_string()
    #BindOb.send_string(reply)
    #print("req:",Rev,"rep:",reply,"dir")
