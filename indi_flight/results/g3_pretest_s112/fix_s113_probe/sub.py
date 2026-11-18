import sys, time
from gz.transport13 import Node
from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.pose_v_pb2 import Pose_V
if len(sys.argv)>2: import gz.msgs10.pose_pb2
n=Node(); got=[]
def cb(m):
    try:
        got.append(("ok",len(m.pose),m.pose[0].name))
    except Exception as e: got.append(("ERR",repr(e)))
print(n.subscribe(Pose_V, sys.argv[1], cb))
time.sleep(8); print(got[:2], len(got))
