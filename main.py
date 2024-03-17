from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app=FastAPI()



inprogress_orders={}





#мы берем текст из DialogFlow, там на сайте можно 
#посмотреть формат отправки поэтому мы берем все необходимые данные
#с этого json ответа сюда
@app.post('/')
async def handle_request(request: Request):
    payload= await request.json()

    
    intent=payload['queryResult']['intent']['displayName']
    parameters=payload['queryResult']
    output_contexts=payload['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])
    
    intent_handler_dict={
        'track.order - context: ongoing-tracking' : track_order,
        'order.add - context: ongoing-order' : add_to_order,
        'order.complete - context: ongoing-order': compelete_order,
        'order.remove - context: ongoing-order' : remove_from_order
    }

    return intent_handler_dict[intent](parameters,session_id)
    



def compelete_order(parameters:dict,session_id:str):
    if session_id not in inprogress_orders:
        fulfillment_text = 'I have trouble to find your order.Can you please make a new one?'
    else:
        order=inprogress_orders[session_id]
        order_id=save_to_db(order)

    
    if order_id == -1:
        fulfillment_text='Sorry, I couldnt process your order. Please try again and make a new order'

    else:
        order_total=db_helper.get_total_order_price(order_id)
        fulfillment_text=f'We have placed your order. Here is your order id {order_id}, your order total is {order_total}' 
       

    del inprogress_orders[session_id]
    
    return JSONResponse(content={
        'fulfillmentText': fulfillment_text
    })

    

def save_to_db(order:dict):
    next_order_id=db_helper.get_next_order_id()
    for food_item,quantity in order.items():
        rcode = db_helper.insert_order_item(food_item,quantity,next_order_id)
        
        if rcode == -1:
            return -1
    
    db_helper.insert_order_tracking(next_order_id,'in progress')
    return next_order_id




def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    
    food_items = parameters['parameters']["food-item"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

      





def add_to_order(parameters:dict,session_id:str):
    food_items=parameters['parameters']['food-item']
    quantities=parameters['parameters']['number']
    
    
    if len(food_items)!=len(quantities):
       fulfillment_text='I DONT UNDERSTAND. Specify food items and quantities clearly'
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]


            #current_food_dict.update(new_food_dict)
            for key, value in new_food_dict.items():
                current_food_dict[key] = current_food_dict.get(key, 0) + value


            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

           
    return JSONResponse(content={
        'fulfillmentText': fulfillment_text
    })




def track_order(parameters:dict,session_id:str):
    
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



