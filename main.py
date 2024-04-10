from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator, root_validator
from typing import Optional
import uuid
import networkx as nx

app = FastAPI(
    title='WorkflowAPI'
)

# Графи для зберігання workflow
workflows = {}
workflows[1] = nx.DiGraph()

@app.post("/workflows/")
async def create_workflow():
    workflow_id = len(workflows) + 1
    workflows[workflow_id] = nx.DiGraph()
    return {"workflow_id": workflow_id} 

@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: int):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    del workflows[workflow_id]
    return {"message": "Workflow deleted"}



def check_workflow_availability(workflow_id, workflows):
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

def check_id_availability(graph, node_id):
    if node_id in graph.nodes:
        raise HTTPException(status_code=400, detail="Node with provided ID in this workflow already created")
    
def check_node_exist(graph, node_id):
    print(node_id)
    print(graph.nodes)
    if node_id in graph.nodes:
        print(1)
        return True
    elif node_id in graph.nodes:
        print(2)
        return False
    # else:
    #     print(3)
    #     raise HTTPException(status_code=500, detail="Unexpected error")

def validate_outgoing_edges(func):
    def wrapper(self, node_id, workflow_id, workflows):
        if len(workflows[workflow_id].successors(node_id)) > 1:
            raise HTTPException(status_code=400, detail="Message node can have only one outgoing edge")
        return func(self, node_id, workflow_id, workflows)
    return wrapper  

def response(msg_: str, type_: str, id_: str, **kwargs) -> dict:
    response = {"message": msg_,
                "type": type_,
                "id": id_}
    
    # Додамо всі передані аргументи (kwargs) в словник відповіді
    response.update(kwargs)

    return response
# def validate_incoming_edges(func):
#     def wrapper(self, node_id, workflow_id, workflows):
#         graph = workflows[workflow_id]
#         if len(graph.predecessors(node_id)) > 1:
#             raise HTTPException(status_code=400, detail="Message node can have multiple incoming edges")
#         return func(self, node_id, workflow_id, workflows)
#     return wrapper

class Node(BaseModel):
    type: Optional[str] = None

class StartNode(Node):
    def __init__(self, graph, node_id):
        super().__init__(type="start")
        graph.add_node(node_id, type="start")
        

class MessageNode(Node):
    type: str = "message"
    status: str
    message: str
    
    @root_validator(pre=True)
    def check_fields(cls, values):
        if values.get('status') is None or values.get('message') is None:
            raise HTTPException(status_code=400, detail="Both values, status and message should be provided")
        return values
    
    @validator('status', pre=True)
    def check_status(cls, status):
        if status not in ['pending', 'sent', 'opened']:
            raise HTTPException(status_code=400, detail="Invalid status. Possible status: pending, sent, opened")
        return status

    # @validate_outgoing_edges
    def add_to_graph(self, graph, node_id):
        graph.add_node(node_id, type="message", status=self.status, message=self.message)

    def add_edge(self, graph, node_id, predecessor_id):
        if check_node_exist(graph, predecessor_id):
            graph.add_edge(node_id, predecessor_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid predecessor id. Node by this ID doesn't exists")
            

class ConditionNode(Node):
    type: str = "condition"

    def add_to_graph(graph, node_id):
        graph.add_node(node_id, type="condition")

class EndNode(Node):
    type: str = "end"

    def add_to_graph(graph, node_id, su):
        if len(graph.successors(node_id)) > 0:
            raise HTTPException(status_code=400, detail="End node can only have one incoming edge")
        graph.add_node(node_id, type="end")


# @app.post("/workflows/{workflow_id}/node/")
# async def add_nodes(workflow_id: int, node_id: str = None):
        
        
StartNode(workflows[1], 1)     


# Функція для додавання нового вузла
@app.post("/workflows/{workflow_id}/nodes/")
async def add_nodes(workflow_id: int, node: Node, node_id: str = None, predecessor: str = None, successor: str = None, status: str = None, message: str = None):
    check_workflow_availability(workflow_id, workflows)
    graph = workflows[workflow_id]
    if not node_id:
        node_id = str(uuid.uuid4())

    check_id_availability(graph, node_id)
    # try:
    if node.type == "start":
        StartNode(graph=graph, node_id=node_id)
        return response("Start node added successfully", "StartNode", node_id)
    elif node.type == "message":
        # print(1)
        message_node = MessageNode(graph=graph, node_id=node_id, status=status, message=message)
        # print(2)
        message_node.add_to_graph(graph, node_id)
        # print(3)
        message_node.add_edge(graph, node_id, predecessor)
        # print(4)
        return response("Message node added successfully", "MessageNode", node_id)
    elif node.type == "condition":
        condition_node = ConditionNode(type="condition")
        condition_node.add_to_graph(graph, node_id)
        return response("Condition node added successfully", "ConditionNode", node_id)
    #     condition_node.add_to_graph(node_id, workflow_id, workflows)
    elif node.type == "end":
        end_node = EndNode(type="end")
        end_node.add_to_graph(graph, node_id, successor)
    # else:
    #     raise HTTPException(status_code=400, detail="Invalid node type")
    # except HTTPException as error:
    #     raise error
    # except:
    #     raise HTTPException(status_code=500, detail="Unexpected Error")
    
    return {"message": "Node added successfully"}







# Додаткові ендпоінти для конфігурації вузлів та запуску workflow будуть додані тут

@app.get("/workflows/")
async def main():
    # for workflow in workflows:
        # print(workflow)
    return workflows

