from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper

app=FastAPI()



inprogress_orders={
}





#мы берем текст из DialogFlow, там на сайте можно 
#посмотреть формат отправки поэтому мы берем все необходимые данные
#с этого json ответа сюда
@app.post('/')
async def handle_request(request: Request):
    payload= await request.json()

    
    intent=payload['queryResult']['intent']['displayName']
    parameters=payload['queryResult']
    output_contexts=payload['queryResult']

    intent_handler_dict={
        'track.order - context: ongoing-tracking' : track_order,
        'order.add - context: ongoing-order' : add_to_order,
        'order.complete - context: ongoing-order': compelete_order,
        'order.remove - context: ongoing-order' : remove_from_order
    }

    return intent_handler_dict[intent](parameters)
    
def compelete_order():
    pass

def remove_from_order():
    pass


def add_to_order(parameters:dict):
    food_items=parameters['parameters']['food-item']
    quantities=parameters['parameters']['number']
    

    if len(food_items)!=len(quantities):
       fulfillment_text='I DONT UNDERSTEND. Specify food items and quantities clearly'
    else:
       fulfillment_text = f'Received {food_items} and {quantities} in the backend'

    return JSONResponse(content={
        'fulfillmentText': fulfillment_text
    })




def track_order(parameters:dict):
    
    order_id=parameters
    print(order_id)
    status=db_helper.get_order_status(order_id)
    
    if status:
        fulfillment_text= f'The order id : {order_id}, order status : {status}'
    else:
        fulfillment_text= f'No order fount with order id : {order_id}'
        
    
    return JSONResponse(content={
            'fulfillmentText' : fulfillment_text
        })   



